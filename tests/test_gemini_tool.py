from app.agent import ORDER_TOOL


def test_order_tool_definition():
    functions = ORDER_TOOL.function_declarations

    assert len(functions) == 1

    tool = functions[0]

    assert tool.name == "lookup_order"
    assert "order_id" in tool.parameters_json_schema["properties"]
    assert "order_id" in tool.parameters_json_schema["required"]