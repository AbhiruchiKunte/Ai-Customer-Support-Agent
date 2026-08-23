from pathlib import Path

from app.documents import parse_document
from app.chunking import create_chunks


KNOWLEDGE_BASE = (
    Path(__file__).resolve().parent.parent
    / "knowledge-base"
)


def test_returns_policy_is_split_into_sections():

    path = (
        KNOWLEDGE_BASE
        / "01-returns-policy-current.md"
    )

    document = parse_document(path)
    chunks = create_chunks(document)

    assert len(chunks) >= 4


def test_chunk_contains_document_metadata():

    path = (
        KNOWLEDGE_BASE
        / "01-returns-policy-current.md"
    )

    document = parse_document(path)
    chunks = create_chunks(document)

    chunk = chunks[0]

    assert chunk["document_id"] == "RET-2026-01"
    assert chunk["status"] == "active"
    assert chunk["audience"] == "customer"
    assert chunk["policy_authority"] == "official"


def test_chunk_contains_heading_and_content():

    path = (
        KNOWLEDGE_BASE
        / "01-returns-policy-current.md"
    )

    document = parse_document(path)
    chunks = create_chunks(document)

    first_chunk = chunks[0]

    assert first_chunk["heading"]
    assert first_chunk["text"]
    assert "Returns Policy" in first_chunk["text"]