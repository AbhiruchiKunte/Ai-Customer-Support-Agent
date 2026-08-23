from typing import List

from app.gemini_client import get_client


EMBEDDING_MODEL = "gemini-embedding-001"


def embed_text(text: str) -> List[float]:
    """Create a Gemini embedding for a piece of text."""

    client = get_client()

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return response.embeddings[0].values