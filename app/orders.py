import json
from pathlib import Path


ORDERS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "orders.json"
)


def load_orders():
    """Load the orders list from the JSON dataset."""
    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["orders"]


def lookup_order(order_id: str):
    """
    Look up an order and return only customer-safe information.

    Order IDs are normalized so that differences in
    capitalization and surrounding whitespace are ignored.
    """

    # Normalize user input
    order_id = order_id.strip().upper()

    orders = load_orders()

    for order in orders:
        stored_order_id = (
            str(order.get("order_id", ""))
            .strip()
            .upper()
        )

        if stored_order_id == order_id:
            status = order.get("status")
            
            # Extract fields
            items = order.get("items")
            placed_at = order.get("placed_at")
            status_updated_at = order.get("status_updated_at")
            shipped_at = order.get("shipped_at")
            delivered_at = order.get("delivered_at")
            carrier = order.get("carrier")
            tracking_number = order.get("tracking_number")
            estimated_delivery = order.get("estimated_delivery")
            customer_safe_message = order.get("customer_safe_message")
            
            # Clear stale fields for cancelled or returned orders
            if status in ("cancelled", "returned"):
                estimated_delivery = None
                if status == "cancelled":
                    carrier = None
                    tracking_number = None
                    shipped_at = None
                    delivered_at = None

            # Only expose customer-safe fields.
            return {
                "order_id": order.get("order_id"),
                "items": items,
                "placed_at": placed_at,
                "status": status,
                "status_updated_at": status_updated_at,
                "shipped_at": shipped_at,
                "delivered_at": delivered_at,
                "carrier": carrier,
                "tracking_number": tracking_number,
                "estimated_delivery": estimated_delivery,
                "customer_safe_message": customer_safe_message,
            }

    return None


if __name__ == "__main__":
    result = lookup_order("ORD-1007")
    print(result)