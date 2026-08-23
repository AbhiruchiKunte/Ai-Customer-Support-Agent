from app.rag import build_context


def test_context_contains_document_id():

    results = [
        {
            "score": 0.8,
            "precedence": 70,
            "final_score": 0.87,
            "chunk": {
                "document_id": "RET-2026-01",
                "filename": "returns.md",
                "title": "Returns Policy",
                "heading": "Standard return window",
                "status": "active",
                "effective_date": "2026-04-01",
                "audience": "customer",
                "policy_authority": "official",
                "text": "Customers may return items within 30 days.",
            },
        }
    ]

    context = build_context(results)

    assert "RET-2026-01" in context
    assert "Standard return window" in context
    assert "30 days" in context