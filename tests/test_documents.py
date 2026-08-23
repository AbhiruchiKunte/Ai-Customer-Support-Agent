from pathlib import Path

from app.documents import parse_document


KNOWLEDGE_BASE = (
    Path(__file__).resolve().parent.parent
    / "knowledge-base"
)


def test_current_returns_policy_metadata():
    path = KNOWLEDGE_BASE / "01-returns-policy-current.md"

    document = parse_document(path)

    assert document["document_id"] == "RET-2026-01"
    assert document["status"] == "active"
    assert document["audience"] == "customer"
    assert document["policy_authority"] == "official"
    assert document["supersedes"] == "RET-2024-01"


def test_legacy_returns_policy_metadata():
    path = KNOWLEDGE_BASE / "02-returns-policy-legacy.md"

    document = parse_document(path)

    assert document["document_id"] == "RET-2024-01"
    assert document["status"] == "superseded"
    assert document["superseded_by"] == "RET-2026-01"


def test_internal_migration_document_cannot_answer_customers():
    path = (
        KNOWLEDGE_BASE
        / "14-internal-content-migration-notes.md"
    )

    document = parse_document(path)

    assert document["audience"] == "internal"
    assert document["policy_authority"] == "none"
    assert document["customer_answering"] is False
    