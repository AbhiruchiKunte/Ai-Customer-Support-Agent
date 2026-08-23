from app.documents import (
    list_documents,
    parse_document,
)

from app.chunking import create_chunks

from app.embeddings import embed_text

from app.vector_store import save_index


def build_index():
    all_chunks = []

    documents = list_documents()

    print(
        f"Found {len(documents)} documents."
    )

    for document_path in documents:

        print(
            f"\nProcessing: "
            f"{document_path.name}"
        )

        document = parse_document(
            document_path
        )

        chunks = create_chunks(
            document
        )

        for chunk in chunks:

            print(
                f"  Embedding: "
                f"{chunk['chunk_id']}"
            )

            embedding = embed_text(
                chunk["text"]
            )

            chunk["embedding"] = embedding

            all_chunks.append(chunk)

    save_index(all_chunks)

    print(
        f"\nCreated {len(all_chunks)} "
        "embedded chunks."
    )


if __name__ == "__main__":
    build_index()