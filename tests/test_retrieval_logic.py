from app.vector_store import cosine_similarity


def test_similar_vectors_rank_higher():

    query = [1.0, 0.0, 0.0]

    relevant = [0.99, 0.01, 0.0]

    irrelevant = [0.0, 1.0, 0.0]

    relevant_score = cosine_similarity(
        query,
        relevant,
    )

    irrelevant_score = cosine_similarity(
        query,
        irrelevant,
    )

    assert relevant_score > irrelevant_score