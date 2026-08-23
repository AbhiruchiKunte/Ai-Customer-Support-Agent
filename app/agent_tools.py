from google.genai import types

from app.orders import lookup_order


def lookup_order_tool(
    order_id: str,
):
    """
    Look up safe customer-facing information
    about an order.
    """

    return lookup_order(order_id)


def search_knowledge_base_tool(
    question: str,
):
    """
    Search the customer-facing knowledge base.
    """

    from app.rag_tool import search_knowledge_base

    return search_knowledge_base(question)


ORDER_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="lookup_order",
            description=(
                "Look up safe customer-facing "
                "information about an order. "
                "Use this when the customer provides "
                "an order ID or asks about an order."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "order_id": types.Schema(
                        type="STRING",
                        description=(
                            "The order ID, such as "
                            "ORD-1001."
                        ),
                    ),
                },
                required=["order_id"],
            ),
        )
    ]
)


RAG_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_knowledge_base",
            description=(
                "Search the Aster & Row customer "
                "knowledge base for policies, "
                "shipping, returns, warranties, "
                "cancellations, membership, "
                "product information, and other "
                "customer-support questions."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "question": types.Schema(
                        type="STRING",
                        description=(
                            "The customer's question "
                            "about Aster & Row policies "
                            "or products."
                        ),
                    ),
                },
                required=["question"],
            ),
        )
    ]
)


TOOLS = [
    ORDER_TOOL,
    RAG_TOOL,
]