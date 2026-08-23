from app.embeddings import embed_text
from app.vector_store import search


TEST_CASES = [
    (
        "What is the return period?",
        "RET-2026-01",
    ),
    (
        "How much is the return shipping fee?",
        "RET-2026-01",
    ),
    (
        "Can I return a final sale item?",
        "RET-2026-02",
    ),
    (
        "Can I cancel my order?",
        "ORD-2026-01",
    ),
    (
        "What is the warranty period?",
        "WAR-2026-01",
    ),
    (
        "What is the TrailPlus return window?",
        "MEM-2026-01",
    ),
]