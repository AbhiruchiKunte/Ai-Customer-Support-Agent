from app.vector_store import cosine_similarity


def test_identical_vectors_have_similarity_one():
    vector = [1.0, 2.0, 3.0]

    score = cosine_similarity(
        vector,
        vector,
    )

    assert abs(score - 1.0) < 0.000001


def test_orthogonal_vectors_have_similarity_zero():
    vector_a = [1.0, 0.0]
    vector_b = [0.0, 1.0]

    score = cosine_similarity(
        vector_a,
        vector_b,
    )

    assert abs(score) < 0.000001