import re
from typing import List, Dict


def split_into_sections(content: str) -> List[Dict]:
    """
    Split Markdown content into sections based on ## headings.

    Each section keeps its heading together with its content.
    """

    lines = content.splitlines()

    sections = []

    current_heading = None
    current_lines = []

    for line in lines:

        # ## Heading
        if re.match(r"^##\s+", line):

            # Save previous section
            if current_heading is not None:
                sections.append(
                    {
                        "heading": current_heading,
                        "content": "\n".join(
                            current_lines
                        ).strip(),
                    }
                )

            current_heading = line.strip("# ").strip()
            current_lines = []

        else:
            current_lines.append(line)

    # Save final section
    if current_heading is not None:
        sections.append(
            {
                "heading": current_heading,
                "content": "\n".join(
                    current_lines
                ).strip(),
            }
        )

    return sections


def create_chunks(document: Dict) -> List[Dict]:
    """
    Convert a parsed document into retrieval chunks.
    """

    sections = split_into_sections(
        document["content"]
    )

    chunks = []

    for index, section in enumerate(sections):

        text = (
            f"# {document['title']}\n\n"
            f"## {section['heading']}\n\n"
            f"{section['content']}"
        )

        chunks.append(
            {
                "chunk_id": (
                    f"{document['document_id']}"
                    f"-{index + 1}"
                ),
                "document_id": document[
                    "document_id"
                ],
                "filename": document["filename"],
                "title": document["title"],
                "heading": section["heading"],
                "status": document["status"],
                "effective_date": document[
                    "effective_date"
                ],
                "last_reviewed": document[
                    "last_reviewed"
                ],
                "audience": document["audience"],
                "policy_authority": document[
                    "policy_authority"
                ],
                "supersedes": document.get("supersedes"),
                "superseded_by": document.get("superseded_by"),
                "superseded_date": document.get("superseded_date"),
                "customer_answering": document[
                    "customer_answering"
                ],
                "text": text,
            }
        )

    return chunks