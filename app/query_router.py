def is_historical_query(query: str) -> bool:
    """
    Detect whether the customer is explicitly asking
    about historical information.
    """

    historical_terms = [
        "2024",
        "2023",
        "previous policy",
        "old policy",
        "former policy",
        "previous return policy",
        "what was the policy",
        "historically",
        "before",
        "earlier policy",
        "legacy policy",
    ]

    query_lower = query.lower()

    return any(
        term in query_lower
        for term in historical_terms
    )