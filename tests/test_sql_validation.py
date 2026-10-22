
import pytest

from app.agents.sql_agent import validate_sql


def test_accepts_select_query():
    query = validate_sql(
        "SELECT name FROM customers"
    )
    assert "SELECT" in query.upper()
    assert "LIMIT 50" in query.upper()


def test_accepts_join():
    query = validate_sql("""
        SELECT c.name, o.status
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        LIMIT 10
    """)
    assert "JOIN" in query.upper()


@pytest.mark.parametrize("query", [
    "DELETE FROM customers",
    "UPDATE customers SET name = 'test'",
    "DROP TABLE customers",
    "SELECT 1; SELECT 2",
    "SELECT * FROM pg_catalog.pg_tables",
    "SELECT * FROM unknown_table",
    "SELECT name FROM customers LIMIT 100",
    "",
])
def test_rejects_unsafe_or_invalid_queries(query):
    with pytest.raises(ValueError):
        validate_sql(query)


def test_rejects_data_modifying_cte():
    query = """
        WITH removed AS (
            DELETE FROM customers RETURNING id
        )
        SELECT * FROM customers
    """
    with pytest.raises(ValueError):
        validate_sql(query)
