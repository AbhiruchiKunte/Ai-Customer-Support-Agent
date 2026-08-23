import json
from pathlib import Path
from typing import List, Dict

import numpy as np


INDEX_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "vector_index.json"
)


def cosine_similarity(
    vector_a: List[float],
    vector_b: List[float],
) -> float:
    """Calculate cosine similarity between two vectors."""

    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)

    denominator = (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b) / denominator
    )


def save_index(chunks: List[Dict]):
    """Save chunks and embeddings to disk."""

    INDEX_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )


def load_index():
    """Load the vector index from disk."""

    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            "Vector index does not exist. "
            "Run the indexing script first."
        )

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def is_customer_safe(chunk: Dict) -> bool:
    """
    Determine whether a chunk is allowed to support
    a customer-facing answer.
    """

    # Internal documents should never be used for
    # normal customer-facing answers.
    if chunk.get("audience") != "customer":
        return False

    # Explicitly prohibited documents are excluded.
    if chunk.get("customer_answering") is False:
        return False

    return True


def precedence_score(chunk: Dict) -> int:
    """
    Give higher priority to authoritative,
    current, customer-facing documents.

    This score is used as a secondary signal
    alongside semantic similarity.
    """

    score = 0

    # Current active policy
    if chunk.get("status") == "active":
        score += 30

    # Official company policy
    if chunk.get("policy_authority") == "official":
        score += 20

    # Customer-facing document
    if chunk.get("audience") == "customer":
        score += 10

    # Explicitly allowed for customer answers
    if chunk.get("customer_answering") is True:
        score += 10

    # Legacy/superseded documents should receive
    # a lower precedence score.
    if chunk.get("status") == "superseded":
        score -= 30

    return score


def search(
    query_embedding: List[float],
    top_k: int = 5,
    customer_only: bool = True,
    min_similarity: float = 0.40,
    historical: bool = False,
):
    """
    Search the vector index using semantic similarity.

    When customer_only=True, internal documents are
    excluded before ranking.

    Final ranking combines:
        1. Semantic similarity
        2. Document precedence
    """

    chunks = load_index()

    # -------------------------------------------------
    # STEP 1: Filter customer-safe documents
    # -------------------------------------------------

    if customer_only:
        chunks = [
            chunk
            for chunk in chunks
            if is_customer_safe(chunk)
        ]

    if not historical:
        chunks = [
        chunk
        for chunk in chunks
        if chunk.get("status") != "superseded"
        ]    

    scored_chunks = []

    # -------------------------------------------------
    # STEP 2: Calculate similarity and precedence
    # -------------------------------------------------

    for chunk in chunks:

        similarity = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        # Ignore chunks that are not sufficiently
        # relevant to the user's question.
        if similarity < min_similarity:
         continue

        precedence = precedence_score(
            chunk
        )

        # Semantic similarity remains the primary
        # retrieval signal.
        #
        # Precedence acts as a smaller bonus/penalty.
        final_score = (
    similarity
    + precedence * 0.001
)

        scored_chunks.append(
            {
                "score": similarity,
                "precedence": precedence,
                "final_score": final_score,
                "chunk": chunk,
            }
        )

    # -------------------------------------------------
    # STEP 3: Rank results
    # -------------------------------------------------

    scored_chunks.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    # -------------------------------------------------
    # STEP 4: Return top results
    # -------------------------------------------------

    return scored_chunks[:top_k]

def evaluate_retrieval(
    query_embedding: List[float],
    expected_document_id: str,
    top_k: int = 5,
    historical: bool = False,
):
    """
    Check whether the expected document appears
    in the top-k retrieval results.
    """

    results = search(
        query_embedding,
        top_k=top_k,
        customer_only=True,
        historical=historical,
    )

    retrieved_ids = [
        result["chunk"]["document_id"]
        for result in results
    ]

    return {
        "expected": expected_document_id,
        "retrieved": retrieved_ids,
        "found": expected_document_id
        in retrieved_ids,
    }