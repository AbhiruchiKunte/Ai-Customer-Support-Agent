from app.agent_tools import lookup_order_tool


def test_lookup_order_tool():

    result = lookup_order_tool("ORD-1001")

    assert result["order_id"] == "ORD-1001"