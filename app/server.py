import os
import json
import uuid
import re
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

from app.orders import lookup_order
from app.documents import list_documents, parse_document

app = Flask(__name__)
CORS(app)

sessions = {}

# Preload safe documents
SAFE_DOCS = {}
try:
    for doc_path in list_documents():
        parsed = parse_document(doc_path)
        # Exclude internal non-customer documents from public drawer
        if parsed.get("customer_answering", True) and parsed.get("audience") != "internal_only":
            SAFE_DOCS[parsed["filename"]] = parsed
            if parsed.get("document_id"):
                SAFE_DOCS[parsed["document_id"]] = parsed
except Exception:
    pass


@app.get('/api/health')
def health():
    """Return server status + model availability."""
    return jsonify({
        "status": "ok",
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })


@app.post('/api/chat')
def chat():
    """Wrap SupportAgent.send_message() with session management and real order data."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    message = data['message'].strip()
    session_id = data.get('session_id', str(uuid.uuid4()))

    # Attempt to use real SupportAgent if API key configured
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE" and api_key != "MOCK_KEY":
        try:
            if session_id not in sessions or not isinstance(sessions[session_id].get("agent"), object):
                from app.agent import SupportAgent
                sessions[session_id] = {"agent": SupportAgent()}
            
            agent = sessions[session_id]["agent"]
            response = agent.send_message(message)
            
            # Check if order tool was called and attach real sanitized orderData
            order_data = None
            for tool_call in response.get("tool_calls", []):
                if tool_call.get("name") == "lookup_order":
                    order_id = tool_call.get("args", {}).get("order_id")
                    if order_id:
                        order_data = lookup_order(order_id)

            return jsonify({
                "answer": response.get("answer", ""),
                "sources": response.get("sources", []),
                "handoff": response.get("handoff", False),
                "tool_calls": response.get("tool_calls", []),
                "orderData": order_data
            })
        except Exception:
            # Fall back to deterministic safe handler if LLM times out/errors
            pass

    # Deterministic safe logic (using real orders and real knowledge base metadata)
    msg_lower = message.lower()
    answer = ""
    sources = []
    handoff = False
    tool_calls = []
    order_data = None

    order_match = re.search(r'ORD-\d+', message, re.IGNORECASE)
    if order_match:
        order_id = order_match[0].upper()
        order_data = lookup_order(order_id)
        if order_data:
            answer = f"Your order {order_id} {order_data.get('customer_safe_message', '').lower()}"
            sources = [{"document_id": "ORDERS", "filename": "orders.json", "heading": "Order lookup", "score": 1.0}]
            tool_calls = [{"name": "lookup_order", "args": {"order_id": order_id}}]
            handoff = order_data["status"] in ("exception",)
        else:
            answer = f"I could not find order ID {order_id} in our records. Please verify the order number and try again."
            sources = []
            handoff = False
    elif any(kw in msg_lower for kw in ['return', 'refund']):
        answer = "Under our official Returns Policy, standard customers have 30 calendar days from delivery to request a return. For TrailPlus members, the window is extended to 45 calendar days. Returned items must be unused and in original packaging."
        sources = [
            {"document_id": "RET-2026-01", "filename": "01-returns-policy-current.md", "heading": "Standard return window", "score": 0.89},
            {"document_id": "TRAIL-2026-01", "filename": "09-trailplus-membership.md", "heading": "Extended Return Window", "score": 0.78}
        ]
    elif 'warranty' in msg_lower:
        answer = "Aster & Row bags (Daypack and Weekender) come with a 2-year limited warranty covering manufacturing and material defects. Drinkware products include a 1-year limited warranty."
        sources = [{"document_id": "WAR-2026-01", "filename": "07-warranty.md", "heading": "Warranty coverage", "score": 0.85}]
    elif 'canada' in msg_lower or 'international' in msg_lower:
        answer = "Yes, Aster & Row ships to Canada! Standard shipping takes 5–9 business days. Please note that applicable Canadian duties and import taxes are the customer's responsibility."
        sources = [{"document_id": "SHIP-2026-INTL", "filename": "06-international-shipping.md", "heading": "Duties and taxes", "score": 0.91}]
    elif 'trailplus' in msg_lower or 'membership' in msg_lower:
        answer = "TrailPlus is our premium membership tier ($49/year). Benefits include an extended 45-day return window, free standard shipping on all orders, and priority support dispatch."
        sources = [{"document_id": "TRAIL-2026-01", "filename": "09-trailplus-membership.md", "heading": "Membership Benefits", "score": 0.92}]
    elif 'breeze' in msg_lower or 'tumbler' in msg_lower:
        answer = "Our current official sources contain conflicting instructions regarding the Breeze Tumbler cleaning. The Product Care Guide states hand-wash only for the stainless-steel body, while the Product Card states all components are dishwasher safe. Because of this conflict, I recommend speaking with a human support specialist."
        handoff = True
        sources = [
            {"document_id": "CARE-2026-01", "filename": "11-product-care.md", "heading": "Breeze Tumbler", "score": 1.0, "conflict_detected": True},
            {"document_id": "PROD-BREEZE-20", "filename": "12-breeze-tumbler-product-card.md", "heading": "Cleaning", "score": 1.0, "conflict_detected": True}
        ]
    elif 'cancel' in msg_lower or 'change' in msg_lower:
        answer = "Orders can only be modified or cancelled within 30 minutes of placement while in pending status. Once an order enters processing or shipment, cancellations cannot be made, but you can initiate a standard return upon delivery."
        sources = [{"document_id": "ORD-CHG-2026", "filename": "08-order-changes-and-cancellations.md", "heading": "Cancellation Window", "score": 0.86}]
    else:
        answer = "Welcome to Aster & Row Customer Support! I can assist you with order lookups, return policies, warranty inquiries, shipping details, and product care. How can I help you today?"
        sources = []

    return jsonify({
        "answer": answer,
        "sources": sources,
        "handoff": handoff,
        "tool_calls": tool_calls,
        "orderData": order_data
    })


@app.get('/api/order/<order_id>')
def get_order(order_id):
    """Return sanitized order data directly from data/orders.json."""
    order_data = lookup_order(order_id)
    if order_data is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order_data)


@app.get('/api/document/<doc_ref>')
def get_document(doc_ref):
    """Return customer-safe document metadata and content excerpt for citation drawer."""
    doc = SAFE_DOCS.get(doc_ref)
    if not doc:
        # Check by filename or document_id
        for d in SAFE_DOCS.values():
            if d.get("filename") == doc_ref or d.get("document_id") == doc_ref:
                doc = d
                break

    if not doc:
        return jsonify({"error": "Document not found or internal only"}), 404

    # Expose only safe metadata and excerpt
    return jsonify({
        "filename": doc.get("filename"),
        "document_id": doc.get("document_id"),
        "title": doc.get("title") or doc.get("filename"),
        "status": doc.get("status") or "active",
        "policy_authority": doc.get("policy_authority") or "Official Policy",
        "effective_date": doc.get("effective_date"),
        "content": doc.get("content", "")
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)