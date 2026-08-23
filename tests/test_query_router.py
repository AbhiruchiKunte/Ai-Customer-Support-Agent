from app.query_router import is_historical_query


def test_current_query_is_not_historical():

    assert (
        is_historical_query(
            "What is the current return policy?"
        )
        is False
    )


def test_2024_query_is_historical():

    assert (
        is_historical_query(
            "What was the return policy in 2024?"
        )
        is True
    )


def test_previous_policy_is_historical():

    assert (
        is_historical_query(
            "What was the previous return policy?"
        )
        is True
    )


def test_normal_question_is_not_historical():

    assert (
        is_historical_query(
            "How much is return shipping?"
        )
        is False
    )