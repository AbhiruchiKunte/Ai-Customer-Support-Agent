from pathlib import Path

import yaml


KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parent.parent
    / "knowledge-base"
)


def list_documents():
    """Return all Markdown documents in the knowledge base."""
    return sorted(KNOWLEDGE_BASE_DIR.glob("*.md"))


def parse_document(path: Path):
    """
    Parse a Markdown document containing YAML front matter.

    Returns structured metadata plus the document content.
    """

    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        raise ValueError(
            f"Document does not contain YAML front matter: "
            f"{path.name}"
        )

    # Split:
    #
    # ---
    # metadata
    # ---
    # content
    #
    parts = text.split("---", 2)

    if len(parts) != 3:
        raise ValueError(
            f"Invalid front matter format: {path.name}"
        )

    metadata_text = parts[1]
    content = parts[2].strip()

    metadata = yaml.safe_load(metadata_text) or {}

    return {
        "filename": path.name,
        "path": str(path),
        "document_id": metadata.get("document_id"),
        "title": metadata.get("title"),
        "status": metadata.get("status"),
        "effective_date": (
            str(metadata.get("effective_date"))
            if metadata.get("effective_date")
            else None
        ),
        "last_reviewed": (
            str(metadata.get("last_reviewed"))
            if metadata.get("last_reviewed")
            else None
        ),
        "audience": metadata.get("audience"),
        "policy_authority": metadata.get(
            "policy_authority"
        ),
        "supersedes": metadata.get("supersedes"),
        "superseded_by": metadata.get(
            "superseded_by"
        ),
        "superseded_date": (
            str(metadata.get("superseded_date"))
            if metadata.get("superseded_date")
            else None
        ),
        "customer_answering": metadata.get(
            "customer_answering",
            True,
        ),
        "content": content,
    }


if __name__ == "__main__":
    documents = list_documents()

    print(f"Found {len(documents)} documents.\n")

    for path in documents:
        document = parse_document(path)

        print("=" * 60)
        print(document["filename"])
        print("=" * 60)

        print(
            f"ID: {document['document_id']}"
        )

        print(
            f"Title: {document['title']}"
        )

        print(
            f"Status: {document['status']}"
        )

        print(
            f"Effective: {document['effective_date']}"
        )

        print(
            f"Audience: {document['audience']}"
        )

        print(
            f"Authority: {document['policy_authority']}"
        )

        print(
            f"Customer answering: "
            f"{document['customer_answering']}"
        )

        print()