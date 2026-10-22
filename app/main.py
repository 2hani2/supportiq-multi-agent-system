
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.db.connection import engine, test_connection
from app.agents.sql_agent import run_sql_agent
from app.agents.rag_agent import answer_policy_question
from app.agents.tool_agent import run_tool_agent
from app.graph.supervisor import run_support_graph
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Agent AI Customer Support",
    description="Customer support powered by LangGraph and RAG",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {"message": "Customer Support AI API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/health/database")
def database_health():
    try:
        return {
            "database": "connected" if test_connection()
            else "unavailable"
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )


@app.get("/orders/{tracking_number}")
def get_order(tracking_number: str):
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
            {"tracking_number": tracking_number},
        ).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return dict(result)


class SQLQuestion(BaseModel):
    question: str


@app.post("/agent/sql")
def sql_agent_endpoint(body: SQLQuestion):
    try:
        return run_sql_agent(body.question)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="SQL agent failed to process the question.",
        )
    
class RAGQuestion(BaseModel):
    question: str


@app.post("/agent/rag")
def rag_agent_endpoint(body: RAGQuestion):
    try:
        return answer_policy_question(body.question)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="RAG agent failed to process the question.",
        )

class ToolQuestion(BaseModel):
    question: str


@app.post("/agent/tools")
def tool_agent_endpoint(body: ToolQuestion):
    try:
        return run_tool_agent(body.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Tool agent failed to process the question."
        )

class SupportQuestion(BaseModel):
    question: str


@app.post("/agent/support")
def support_endpoint(body: SupportQuestion):
    try:
        return run_support_graph(body.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Customer support request failed."
        )
