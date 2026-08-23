from app.rag import answer_question


def search_knowledge_base(
    question: str,
) -> dict:
    """
    Search the Aster & Row knowledge base and return
    a grounded answer with its sources.
    """

    result = answer_question(
        question,
        top_k=8,
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "conflict_detected": result.get("conflict_detected", False),
    }