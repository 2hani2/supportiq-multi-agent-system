
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"].lower() == (
        "customer support ai api is running"
    )


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_health():
    response = client.get("/health/database")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_empty_support_question():
    response = client.post(
        "/agent/support",
        json={"question": ""},
    )
    assert response.status_code == 400


def test_missing_support_question():
    response = client.post("/agent/support", json={})
    assert response.status_code == 422


def test_supervisor_routes_policy_question_to_rag():
    with patch(
        "app.graph.supervisor.classify_question",
        return_value="rag",
    ), patch(
        "app.graph.supervisor.answer_policy_question",
        return_value={
            "question": "What is the refund policy?",
            "answer": "Returns are accepted within 7 days.",
            "sources": ["refund_policy.txt"],
        },
    ):
        from app.graph.supervisor import run_support_graph

        result = run_support_graph("What is the refund policy?")

    assert result["selected_agent"] == "rag"
    assert "7 days" in result["answer"]


def test_supervisor_routes_order_question_to_tools():
    with patch(
        "app.graph.supervisor.classify_question",
        return_value="tools",
    ), patch(
        "app.graph.supervisor.run_tool_agent",
        return_value={
            "question": "What is the status of TRK1001?",
            "answer": "The order has shipped.",
            "tool_results": [],
        },
    ):
        from app.graph.supervisor import run_support_graph

        result = run_support_graph(
            "What is the status of TRK1001?"
        )

    assert result["selected_agent"] == "tools"
    assert "shipped" in result["answer"]

