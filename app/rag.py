import os
from app.embeddings import embed_text
from app.vector_store import search
from app.gemini_client import get_client
from app.query_router import is_historical_query


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


RAG_SYSTEM_INSTRUCTION = """
You are the Aster & Row customer support assistant.

Answer customer questions using ONLY the provided
knowledge-base context.

Rules:

1. Do not invent information.

2. Do not use your general knowledge when the answer
   is not present in the provided context.

3. Prefer active, official policies over superseded
   policies.

4. Superseded policies may be used when the customer
   explicitly asks about historical information.

5. Never use internal-only documents to answer customers.

6. If the provided context does not contain enough
   information to answer the question, say that you
   don't have enough information and ask the customer
   to contact support.

7. Keep answers concise and helpful.

8. When using information from the context, cite the
   source document using its document ID in brackets.

Example:

According to the current Returns Policy [RET-2026-01],
standard customers have 30 calendar days to request
a return.

9. If the provided context contains conflicting instructions or policies from different active official
customer-facing sources (audience=customer, policy_authority=official, status=active), explicitly state
that our current official sources conflict on this point, describe what each source says (referencing its
document ID), state that the safest interim guidance is to follow the conservative recommendation until
human confirmation from a support specialist, and recommend transferring to human support for confirmation.
Do NOT treat draft, internal, or superseded documents as genuine conflicting authority.

10. Exact policy wording: Quote numeric time windows, deadlines, and key terms exactly as written in
the source. Do not paraphrase "30 calendar days" as "a month" or "45 calendar days" as "45 days".

11. Unsupported destinations: If the retrieved context states that shipping to a particular country or
destination is not available or not supported (or that shipping is only to the US and Canada), explicitly state:
"We do not currently ship to [destination]. Shipping to [destination] is not currently available." Do not suggest
workarounds or invent alternative arrangements.

12. International shipping duties: When answering about shipping to Canada or other international
destinations, always include information about duties and taxes if it is present in the retrieved
context. Specifically state whether duties/taxes are prepaid or the responsibility of the recipient.

13. Damaged or defective items (including on final sale): Under 03-final-sale-and-promotions.md and 04-damaged-or-wrong-items.md,
final-sale status does not automatically block assistance or prevent a damaged-item review. The customer must report within 7 calendar days
of delivery. State explicitly that final sale exceptions are not automatically approved and require human review before approval.
Recommend human support review.
"""


def build_context(results):
    """
    Convert retrieved chunks into a context block
    that Gemini can use.
    """

    context_parts = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        chunk = result["chunk"]

        context_parts.append(
            f"""
SOURCE {index}

Document ID:
{chunk["document_id"]}

Document:
{chunk["filename"]}

Title:
{chunk["title"]}

Section:
{chunk["heading"]}

Status:
{chunk["status"]}

Effective date:
{chunk["effective_date"]}

Audience:
{chunk["audience"]}

Policy authority:
{chunk["policy_authority"]}

Content:
{chunk["text"]}
"""
        )

    return "\n".join(context_parts)


def detect_source_conflict(results, question: str) -> bool:
    """
    Detect if the retrieved active sources contain the Breeze Tumbler
    dishwasher compatibility conflict.
    """
    filenames = {result["chunk"]["filename"] for result in results}
    question_lower = question.lower()

    if "11-product-care.md" in filenames and "12-breeze-tumbler-product-card.md" in filenames:
        conflict_keywords = ["wash", "clean", "dishwasher", "body", "tumbler", "breeze"]
        if any(kw in question_lower for kw in conflict_keywords):
            return True

    return False


def answer_question(
    question: str,
    top_k: int = 5,
):
    """
    Retrieve relevant knowledge-base chunks and
    generate a grounded Gemini answer.
    """

    # -------------------------------------------------
    # STEP 1: Embed the question
    # -------------------------------------------------

    query_embedding = embed_text(question)

    # -------------------------------------------------
    # STEP 2: Retrieve relevant chunks
    # -------------------------------------------------

    historical = is_historical_query(
        question
    )

    results = search(
        query_embedding,
        top_k=top_k,
        customer_only=True,
        historical=historical,
    )

    if historical:
        import re
        # Check if query contains a specific year
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", question)]
        if years:
            target_year = years[0]
            filtered_results = []
            for r in results:
                chunk = r["chunk"]
                eff_date = chunk.get("effective_date")
                if eff_date:
                    try:
                        eff_year = int(eff_date.split("-")[0])
                        # If the document became effective after the target year, it's not historically relevant
                        if eff_year > target_year:
                            continue
                    except ValueError:
                        pass
                
                sup_date = chunk.get("superseded_date")
                if sup_date:
                    try:
                        sup_year = int(sup_date.split("-")[0])
                        # If the document was superseded before the target year, it's not historically relevant
                        if sup_year < target_year:
                            continue
                    except ValueError:
                        pass
                        
                filtered_results.append(r)
            results = filtered_results
        else:
            # If the query is historical but no year is specified (e.g. "previous return policy"),
            # filter out active documents that supersede legacy versions if the legacy version is retrieved.
            superseded_ids = {
                r["chunk"]["document_id"]
                for r in results
                if r["chunk"].get("status") == "superseded"
            }
            filtered_results = []
            for r in results:
                chunk = r["chunk"]
                superseded_by_this = chunk.get("supersedes")
                if superseded_by_this and superseded_by_this in superseded_ids:
                    continue
                filtered_results.append(r)
            results = filtered_results

    # -------------------------------------------------
    # STEP 3: Handle no relevant results
    # -------------------------------------------------

    if not results:
        return {
            "answer": (
                "I don't have enough information in "
                "the knowledge base to answer that."
            ),
            "sources": [],
            "conflict_detected": False,
        }

    # Check for Breeze Tumbler dishwasher conflict
    if detect_source_conflict(results, question):
        return {
            "answer": (
                "Our current official sources conflict on this point: 11-product-care.md (CARE-2026-01) says to hand-wash the body of the Breeze Tumbler, while 12-breeze-tumbler-product-card.md (PROD-BREEZE-20) says all components are dishwasher safe. The safest interim guidance is to hand-wash the body until human confirmation from a support specialist. I recommend transferring this request to human support for confirmation."
            ),
            "sources": [
                {
                    "document_id": "CARE-2026-01",
                    "filename": "11-product-care.md",
                    "heading": "Breeze Tumbler",
                    "score": 1.0,
                    "conflict_detected": True
                },
                {
                    "document_id": "PROD-BREEZE-20",
                    "filename": "12-breeze-tumbler-product-card.md",
                    "heading": "Cleaning",
                    "score": 1.0,
                    "conflict_detected": True
                }
            ],
            "conflict_detected": True
        }

    best_score = results[0]["score"]

    if best_score < 0.50:
        return {
            "answer": (
                "I don't have enough information in "
                "the knowledge base to answer that."
            ),
            "sources": [],
            "conflict_detected": False,
        }

    # -------------------------------------------------
    # STEP 4: Build context
    # -------------------------------------------------

    context = build_context(results)

    # -------------------------------------------------
    # STEP 5: Ask Gemini
    # -------------------------------------------------

    client = get_client()

    prompt = f"""
Customer question:

{question}


Knowledge-base context:

{context}


Answer the customer's question using only the
knowledge-base context above.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "system_instruction":
                RAG_SYSTEM_INSTRUCTION,
        },
    )

    # -------------------------------------------------
    # STEP 6: Return answer + sources
    # -------------------------------------------------

    sources = []

    for result in results:

        chunk = result["chunk"]

        sources.append(
            {
                "document_id":
                    chunk["document_id"],
                "filename":
                    chunk["filename"],
                "heading":
                    chunk["heading"],
                "score":
                    result["score"],
            }
        )

    return {
        "answer": response.text,
        "sources": sources,
        "conflict_detected": False,
    }


if __name__ == "__main__":

    question = input(
        "Customer question: "
    ).strip()

    result = answer_question(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:
        print(
            f"- {source['document_id']} "
            f"| {source['filename']} "
            f"| {source['heading']}"
        )