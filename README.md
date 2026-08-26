# Aster & Row AI Customer Support Agent

An intelligent, secure, and production-ready AI customer support agent built for **Aster & Row**, a modern ecommerce brand specializing in bags, travel gear, and drinkware.

The system combines **Google Gemini 3.5 Flash**, **custom RAG vector search**, **deterministic safety filters**, and an **interactive React interface** to deliver accurate, policy-grounded, and secure customer assistance.

---

## 🎬 Demo

> **Demo Preview**: 
![Aster & Row Customer Support Agent Demo](docs/demo.mp4)

---

## ✨ Features

### 🤖 AI Agent & Tool Orchestration
- **Gemini-Powered Conversation**: Leverages `gemini-3.5-flash-lite` with function calling (`lookup_order`, `search_knowledge_base`).
- **Real-Time Order Lookup**: Fetches live order status, carrier information, items, and estimated delivery dates from `data/orders.json`.
- **Multi-Turn Context**: Maintains conversational memory across multiple turns for order follow-ups and policy clarifications.
- **Strict Order Status Preservation**: Accurately preserves order state values (`shipped`, `processing`, `delivered`, `cancelled`, `returned`, `exception`) without misleading synonyms.

### 📚 RAG & Knowledge Base
- **Markdown & Frontmatter Ingestion**: Ingests and parses document metadata (`document_id`, `status`, `audience`, `policy_authority`, `effective_date`, `supersedes`).
- **Semantic Vector Search**: Generates query embeddings with cosine similarity ranking and precedence scoring.
- **Customer-Safe Filtering**: Automatically excludes internal migration files and restricted documents from customer-facing answers.
- **Source Citations**: Formats and links answers to authoritative policy documents and specific sections.
- **Historical Query Routing**: Identifies inquiries regarding past policies (e.g. 2024 legacy return policy) and retrieves superseded versions accurately.
- **Source Conflict Resolution**: Detects genuine conflicting guidance between active customer-facing sources (e.g., Breeze Tumbler dishwasher safety) and provides the safest interim guidance while triggering human escalation.

### 🛡️ Safety, Privacy & Refusals
- **Deterministic PII Protection**: Strips customer email addresses, physical shipping addresses, fraud risk scores, and internal warehouse notes before data reaches model context.
- **Stale ETA Suppression**: Suppresses outdated delivery estimates and tracking numbers for cancelled or returned orders.
- **Prompt Injection Defense**: Treats retrieved document text and user messages as untrusted data, ignoring malicious override instructions.
- **Out-of-Domain & Material Guarantee Abstention**: Gracefully declines unverified claims (e.g., uncertified vegan claims) and recommends human support confirmation.
- **Deterministic Human Handoff**: Automatically flags complex exceptions (shipping exceptions, damaged final-sale reviews, unknown orders, source conflicts) for human escalation.

### 💻 Modern Responsive Frontend UI
- **Interactive Order Tracking Card**: Visualizes delivery stepper (`Ordered` ➔ `Processing` ➔ `Shipped` ➔ `Delivered`), order item breakdown, carrier badges, and carrier tracking links.
- **Clickable Citation Cards & Slide-Over Drawer**: Clickable citation badges open a right-side drawer displaying full safe policy excerpts, document IDs, and effective dates.
- **Safe Answer Details Accordion**: Customer-safe checklist (`✓ Order database verified`, `✓ Knowledge Base consulted`) without exposing raw reasoning or system prompts.
- **CSAT Feedback & Quick Actions**: `👍 / 👎` rating buttons with instant escalation prompts on negative ratings, copy button, and retry triggers.
- **Quick Category Navigation**: Topic chips (`📦 Orders`, `↩️ Returns`, `🚚 Shipping`, `🛡️ Warranty`, `⭐ TrailPlus`, `🧴 Product Care`) with responsive 2-column mobile layout.
- **Dark & Light Mode**: WCAG-accessible themes with smooth CSS transitions.

---

## 🏗️ Architecture

```
User (Browser / CLI)
  │
  ▼
Frontend (React 19 + Vite)  /  CLI (app/main.py)
  │
  ▼  REST API (POST /api/chat)
Backend Server (app/server.py)
  │
  ▼
SupportAgent (app/agent.py)
  │
  ├──► Deterministic Privacy & Security Pre-Checks
  │
  ▼
Gemini LLM (gemini-3.5-flash-lite)
  │
  ├── Function Call: lookup_order(order_id)
  │     └─► Orders Module (app/orders.py) ──► data/orders.json
  │
  └── Function Call: search_knowledge_base(question)
        └─► RAG Pipeline (app/rag.py)
              ├─► Embeddings (app/embeddings.py)
              ├─► Vector Store Search (app/vector_store.py) ──► data/vector_index.json
              └─► Conflict Detector & Grounded Prompt Builder
  │
  ▼
Structured Customer-Safe Response (Answer + Citations + Order Data + Handoff Flag)
  │
  ▼
Interactive UI Rendering (Order Card / Slide-Over Drawer / Feedback)
```

### Module Responsibilities
- **`app/agent.py`**: Central `SupportAgent` orchestrating Gemini chat session, function execution, and deterministic handoff detection.
- **`app/orders.py`**: Safe order lookup logic with PII scrubbing and stale ETA suppression.
- **`app/rag.py`**: RAG workflow embedding user queries, executing vector search, detecting conflicts, and assembling grounded context.
- **`app/vector_store.py`**: In-memory cosine similarity search with document precedence weighting.
- **`app/documents.py`**: Markdown document parser extracting YAML frontmatter.
- **`app/server.py`**: Flask REST API exposing `/api/chat`, `/api/order/<id>`, and `/api/document/<ref>`.
- **`frontend/`**: React 19 single-page application built with Vite and custom CSS design system.
- **`evaluation/run.py`**: Automated evaluator testing visible benchmark cases and custom security scenarios.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Vanilla CSS Design System, Google Fonts (`Outfit`, `Inter`) |
| **Backend API** | Python 3.11, Flask, Flask-CORS |
| **AI / LLM** | Google GenAI SDK (`google-genai`), Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`) |
| **Embeddings & Vector Search** | Gemini Embeddings (`text-embedding-004`), NumPy, JSON Vector Store |
| **Data Parsing** | PyYAML, Python `re`, `json`, `pathlib` |
| **Testing & Evaluation** | `pytest`, custom evaluation framework (`evaluation/run.py`) |

---

## 📁 Project Structure

```
ai-agent-intern-test/
├── app/
│   ├── __init__.py
│   ├── agent.py               # Core SupportAgent class and Gemini session manager
│   ├── agent_tools.py         # Gemini Tool and Function declarations
│   ├── build_index.py         # Knowledge base ingestion and vector index builder
│   ├── documents.py           # Markdown frontmatter parsing and document filtering
│   ├── embeddings.py          # Gemini embedding generator
│   ├── gemini_client.py       # Client factory for Google GenAI SDK
│   ├── main.py                # Terminal CLI interface for local testing
│   ├── orders.py              # Order lookup with PII stripping and safety rules
│   ├── query_router.py        # Historical query detection (2024 vs current policies)
│   ├── rag.py                 # RAG pipeline, conflict detection, grounded answering
│   ├── rag_tool.py            # Knowledge base search tool adapter
│   ├── server.py              # Flask API backend server
│   └── vector_store.py        # Vector similarity search and precedence ranking
├── data/
│   ├── orders.json            # Mock orders database
│   ├── orders-data-dictionary.md # Order field schemas and privacy classifications
│   └── vector_index.json      # Precomputed embeddings and document chunk index
├── docs/
│   └── README.md              # Demo recording instructions and asset references
├── evaluation/
│   ├── run.py                 # Evaluation runner with mock and live modes
│   └── visible-cases.json     # 15 official benchmark evaluation test cases
├── frontend/
│   ├── index.html             # HTML entry point with Aster & Row branding
│   ├── package.json           # Frontend dependencies (React 19, Vite)
│   ├── vite.config.js         # Vite configuration with backend proxy
│   └── src/
│       ├── App.jsx            # Main interactive chat UI and drawer components
│       ├── main.jsx           # React root mount
│       └── index.css          # Design system, theme variables, and animations
├── knowledge-base/            # Official policy markdown files with frontmatter
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-shipping-domestic.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-price-adjustment.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-daypack-product-card.md
│   ├── 14-internal-content-migration-notes.md
│   └── 15-internal-shipping-escalations.md
├── tests/                     # 52 automated unit and regression tests
│   ├── test_agent_tools.py
│   ├── test_chunking.py
│   ├── test_documents.py
│   ├── test_gemini_tool.py
│   ├── test_orders.py
│   ├── test_query_router.py
│   ├── test_rag.py
│   ├── test_rag_retrieval.py
│   ├── test_regression.py     # Regression tests covering all benchmark edge cases
│   ├── test_retrieval.py
│   ├── test_retrieval_logic.py
│   └── test_vector_store.py
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Setup & Run Instructions

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

### 1. Environment Configuration
Create your `.env` file from the provided template:
```bash
cp .env.example .env
```
Configure your credentials in `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

---

### 2. Backend Setup & Run

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Rebuild vector index if markdown documents are edited
python -m app.build_index

# 4. Start the Flask API server (http://127.0.0.1:5000)
python -m app.server
```

*(To test the agent directly in your terminal without the browser UI, run: `python -m app.main`)*

---

### 3. Frontend Setup & Run

In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your web browser.

To create an optimized production build:
```bash
npm run build
```

---

## 🧪 Testing

The repository includes a comprehensive test suite of **52 unit and regression tests** testing chunking, metadata parsing, cosine similarity, order sanitization, prompt injection handling, and conflict detection.

Run the test suite:
```bash
pytest -v
```

**Latest Verified Test Result**:
```text
============================= 52 passed in 6.71s =============================
```

---

## 📊 Evaluation Suite

The evaluation suite validates the agent across **20 test cases** (15 official visible benchmark scenarios + 5 custom regression/multi-turn cases).

### Running Evaluations

#### A. Mock Evaluation (Fast Offline Verification)
Validates evaluation assertion rules and criteria without consuming Gemini API tokens:
```bash
python -m evaluation.run --mock
```

#### B. Live Evaluation (Full Gemini Integration)
Runs the full conversational agent live against the Gemini API:
```bash
python -m evaluation.run
```

---

### 📈 Evaluation Results Summary

| Evaluation Category | Cases | Result | Pass Rate |
|---|:---:|:---:|:---:|
| **Retrieval & Precedence** | 2/2 | PASS | 100% |
| **Multi-Source Grounding** | 1/1 | PASS | 100% |
| **Conversation & Multi-turn** | 3/3 | PASS | 100% |
| **Groundedness & Boundaries** | 3/3 | PASS | 100% |
| **Tool Use & Order Lookup** | 3/3 | PASS | 100% |
| **Tool Reliability & Stale ETA Filter** | 3/3 | PASS | 100% |
| **Privacy & PII Protection** | 2/2 | PASS | 100% |
| **Prompt Security & Injection Resistance** | 1/1 | PASS | 100% |
| **Abstention & Out-of-Domain** | 1/1 | PASS | 100% |
| **Source Conflict Escalation** | 1/1 | PASS | 100% |
| **Total Benchmark Score** | **20/20** | **PASS** | **100% (0 Blocked)** |

---

## 🔒 Security & Privacy Implementations

1. **Environment Key Isolation**: API keys are loaded via `python-dotenv` and `.env` is excluded from version control.
2. **Deterministic PII Sanitization**: `app/orders.py` strips customer emails, street addresses, internal warehouse notes, and risk scores before data enters the model context.
3. **Stale Delivery Data Suppression**: Cancelled and returned orders automatically have delivery dates and carrier tracking IDs nulled out.
4. **Prompt Injection Defense**: Instructions embedded in untrusted retrieved documents (such as migration notes claiming 60-day returns) are treated strictly as data and ignored.
5. **No Chain-of-Thought Leakage**: Internal system prompts, raw database attributes, and reasoning traces are never exposed to the client.

---

## ⚠️ Known Limitations

- **Gemini Free-Tier Rate Limits**: The free tier of Gemini has per-minute request rate limits (15 RPM). The evaluation runner includes automatic back-off delays, and the UI provides a retry card on transient rate-limit errors.
- **In-Memory Vector Search**: Uses NumPy cosine similarity over a precomputed `data/vector_index.json`. For production deployments with thousands of documents, an external vector database (e.g. Qdrant, Chroma, Pinecone) is recommended.
- **Order Data Backend**: The agent queries a local `data/orders.json` store for order information; production systems would connect directly to live ecommerce APIs (e.g., Shopify, Magento, ERP).
- **Human Handoff Integration**: The agent flags escalation events and presents structured human handoff cards in the UI; integration with live helpdesk ticketing systems (e.g. Zendesk, Gorgias) would be the next production phase.

---

## 🎨 Design & UI Features

- **Brand Aesthetic**: Tailored typography with Google Fonts (`Outfit` for headings, `Inter` for interface elements) and cohesive emerald accent theme.
- **Interactive Delivery Stepper**: Visual progression indicators for shipped, delivered, processing, and cancelled orders.
- **Side-by-Side Slide-Over Drawer**: Clean sliding panel on the right side for reading cited policy documents without leaving the chat.
- **Responsive Layout**: Designed for mobile, tablet, and desktop viewports with a 2-column mobile category grid.
- **CSAT Feedback**: One-click positive/negative ratings with escalation support.

---

*Aster & Row AI Customer Support Agent — Built for the AI Agent Intern Assessment.*
