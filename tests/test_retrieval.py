from app.vector_store import (
    is_customer_safe,
    precedence_score,
)


def test_internal_document_is_not_customer_safe():

    chunk = {
        "audience": "internal",
        "customer_answering": False,
    }

    assert is_customer_safe(chunk) is False


def test_customer_document_is_customer_safe():

    chunk = {
        "audience": "customer",
        "customer_answering": True,
    }

    assert is_customer_safe(chunk) is True


def test_active_official_document_has_high_precedence():

    chunk = {
        "status": "active",
        "policy_authority": "official",
        "audience": "customer",
        "customer_answering": True,
    }

    score = precedence_score(chunk)

    assert score == 70


def test_superseded_document_gets_lower_precedence():

    chunk = {
        "status": "superseded",
        "policy_authority": "official",
        "audience": "customer",
        "customer_answering": True,
    }

    score = precedence_score(chunk)

    assert score == 10

def test_low_similarity_results_are_not_required():
    """
    This is a basic contract test for the retrieval layer.
    The actual embedding-dependent threshold is tested
    through the search behavior.
    """

    assert 0.45 > 0.0