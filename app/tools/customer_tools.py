
from sqlalchemy import text

from app.db.connection import engine


def lookup_order(tracking_number: str) -> dict:
    """Look up an order using its tracking number."""

    query = text("""
        SELECT
            c.name AS customer_name,
            o.product_name,
            o.status,
            o.amount,
            o.tracking_number,
            o.order_date
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.tracking_number = :tracking_number
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"tracking_number": tracking_number.strip()}
        ).mappings().first()

    if result is None:
        return {
            "found": False,
            "message": "No order was found with that tracking number."
        }

    return {
        "found": True,
        "order": {
            key: str(value) if value is not None else None
            for key, value in result.items()
        }
    }


def lookup_customer_tickets(customer_name: str) -> dict:
    """Find support tickets belonging to a customer."""

    query = text("""
        SELECT
            c.name AS customer_name,
            t.subject,
            t.status,
            t.priority,
            t.created_at
        FROM support_tickets t
        JOIN customers c ON c.id = t.customer_id
        WHERE LOWER(c.name) = LOWER(:customer_name)
        ORDER BY t.created_at DESC
    """)

    with engine.connect() as connection:
        results = connection.execute(
            query,
            {"customer_name": customer_name.strip()}
        ).mappings().all()

    if not results:
        return {
            "found": False,
            "message": "No support tickets were found for that customer."
        }

    tickets = [
        {
            key: str(value) if value is not None else None
            for key, value in row.items()
        }
        for row in results
    ]

    return {
        "found": True,
        "tickets": tickets
    }
