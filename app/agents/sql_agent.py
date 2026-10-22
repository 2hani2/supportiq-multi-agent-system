
import os
import re
import sqlglot


from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import create_engine, text
from sqlglot import exp


DATABASE_URL = os.environ["SQL_AGENT_DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"],
)

SCHEMA = """
Tables:

customers(
    id, name, email, created_at
)

orders(
    id, customer_id, product_name, order_date,
    status, amount, tracking_number
)

support_tickets(
    id, customer_id, subject, description,
    status, priority, created_at
)

Relationships:
orders.customer_id = customers.id
support_tickets.customer_id = customers.id
"""


def generate_sql(question: str) -> str:
    response = llm.invoke([
        SystemMessage(content=f"""
You are a PostgreSQL query generator for a customer support system.

Schema:
{SCHEMA}

Rules:
- Generate exactly one SELECT statement.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
  CREATE, TRUNCATE, GRANT, or other modifying statements.
- Do not query system catalogs or database metadata.
- Use only the tables and columns in the supplied schema.
- Use explicit JOIN conditions.
- Limit results to 50 rows.
- Return only SQL, without markdown fences or explanations.
"""),
        HumanMessage(content=question),
    ])

    return response.content.strip()



ALLOWED_TABLES = {
    "customers",
    "orders",
    "support_tickets",
}


def validate_sql(query: str) -> str:
    query = query.strip()

    if not query:
        raise ValueError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(query, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("Invalid SQL syntax.") from exc

    # Reject multiple statements and empty input.
    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    parsed = statements[0]

    # Only a SELECT statement may be the root query.
    if not isinstance(parsed, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject modifying statements, including ones nested in CTEs.
    forbidden_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.Merge,
        exp.Command,
    )

    if any(parsed.find_all(*forbidden_types)):
        raise ValueError("Query contains a forbidden operation.")

    # Restrict tables to the application's known schema.
    for table in parsed.find_all(exp.Table):
        if (
            table.name.lower() not in ALLOWED_TABLES
            or table.db
            or table.catalog
        ):
            raise ValueError(
                "Query references a table outside the allowed schema."
            )

    # Reject locking clauses.
    if parsed.args.get("locks"):
        raise ValueError("Locking queries are not allowed.")

    # Apply a maximum result limit.
    limit = parsed.args.get("limit")

    if limit is None:
        parsed = parsed.limit(50)
    else:
        limit_value = limit.expression

        if not isinstance(limit_value, exp.Literal) or limit_value.is_string:
            raise ValueError("LIMIT must be a numeric literal.")

        try:
            limit_number = int(limit_value.this)
        except (TypeError, ValueError) as exc:
            raise ValueError("LIMIT must be a numeric literal.") from exc

        if limit_number < 1 or limit_number > 50:
            raise ValueError("LIMIT must be between 1 and 50.")

    return parsed.sql(dialect="postgres")


def run_sql_agent(question: str) -> dict:
    sql = validate_sql(generate_sql(question))

    # A read-only, read-committed transaction is an additional safeguard.
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '5s'"))

            result = connection.execute(text(sql))
            rows = [dict(row) for row in result.mappings().all()]

    return {
        "question": question,
        "sql": sql,
        "results": rows,
    }
