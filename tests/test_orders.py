from app.orders import lookup_order


def test_valid_order():
    result = lookup_order("ORD-1001")

    assert result is not None
    assert result["order_id"] == "ORD-1001"


def test_lowercase_order_id():
    result = lookup_order("ord-1001")

    assert result is not None
    assert result["order_id"] == "ORD-1001"


def test_order_id_with_spaces():
    result = lookup_order("  ORD-1001  ")

    assert result is not None
    assert result["order_id"] == "ORD-1001"


def test_unknown_order():
    result = lookup_order("ORD-999999")

    assert result is None


def test_private_information_is_not_exposed():
    result = lookup_order("ORD-1001")

    assert "customer" not in result
    assert "email" not in result
    assert "shipping_address" not in result
    assert "internal" not in result
    assert "risk_score" not in result
    assert "warehouse_note" not in result