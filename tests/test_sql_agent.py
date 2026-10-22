
from unittest.mock import MagicMock, patch

import pytest

from app.agents.sql_agent import run_sql_agent


@patch("app.agents.sql_agent.engine")
@patch("app.agents.sql_agent.generate_sql")
def test_sql_agent_returns_query_results(
    mock_generate_sql,
    mock_engine,
):
    mock_generate_sql.return_value = (
        "SELECT name FROM customers LIMIT 10"
    )

    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = (
        mock_connection
    )

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"name": "Aarav Sharma"}
    ]

    mock_connection.execute.side_effect = [
        None,  # SET TRANSACTION READ ONLY
        None,  # SET LOCAL statement_timeout
        mock_result,  # Execute SELECT
    ]

    result = run_sql_agent("List a customer")

    assert result["question"] == "List a customer"
    assert result["results"] == [{"name": "Aarav Sharma"}]
    assert "LIMIT 10" in result["sql"].upper()
    assert mock_connection.execute.call_count == 3


@patch("app.agents.sql_agent.engine")
@patch("app.agents.sql_agent.generate_sql")
def test_sql_agent_rejects_invalid_query_before_execution(
    mock_generate_sql,
    mock_engine,
):
    mock_generate_sql.return_value = "DELETE FROM customers"

    with pytest.raises(ValueError):
        run_sql_agent("Delete a customer")

    mock_engine.connect.assert_not_called()
