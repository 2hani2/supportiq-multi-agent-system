
from typing import Literal, TypedDict

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

import os

from app.agents.sql_agent import run_sql_agent
from app.agents.rag_agent import answer_policy_question
from app.agents.tool_agent import run_tool_agent


class SupportState(TypedDict):
    question: str
    route: str
    answer: str
    agent_result: dict


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"],
)


def classify_question(question: str) -> str:
    response = llm.invoke([
        SystemMessage(content="""You are a routing classifier for a customer support system.

Choose exactly one route:
- sql: questions about customer records, order lists, order history, or database information.
- rag: questions about refund rules, shipping policies, delivery timeframes, or policy documents.
- tools: questions requiring a specific order lookup by tracking number or a customer's support-ticket lookup.

Return only one word: sql, rag, or tools.
"""),
        HumanMessage(content=question),
    ])

    route = response.content.strip().lower()

    if route not in {"sql", "rag", "tools"}:
        raise ValueError(f"Unexpected supervisor route: {route}")

    return route


def supervisor_node(state: SupportState) -> dict:
    route = classify_question(state["question"])
    return {"route": route}



def sql_node(state: SupportState) -> dict:
    result = run_sql_agent(state["question"])

    response = llm.invoke([
        SystemMessage(content="""You are a customer support assistant.
Convert the supplied SQL query results into a concise, friendly answer.
Use only the data in the results. Never invent details.
If the results are empty, clearly say no matching records were found.
Do not expose SQL queries or internal database details to the customer.
Format currency in Indian rupees when appropriate.
"""),
        HumanMessage(content=(
            f"Customer question: {state['question']}\n\n"
            f"Database results: {result.get('results', [])}"
        )),
    ])

    return {
        "answer": response.content,
        "agent_result": result,
    }



def rag_node(state: SupportState) -> dict:
    result = answer_policy_question(state["question"])
    return {
        "answer": result.get("answer", str(result)),
        "agent_result": result,
    }


def tools_node(state: SupportState) -> dict:
    result = run_tool_agent(state["question"])
    return {
        "answer": result.get("answer", str(result)),
        "agent_result": result,
    }


def route_to_agent(
    state: SupportState,
) -> Literal["sql", "rag", "tools"]:
    return state["route"]


graph_builder = StateGraph(SupportState)

graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("sql", sql_node)
graph_builder.add_node("rag", rag_node)
graph_builder.add_node("tools", tools_node)

graph_builder.add_edge(START, "supervisor")

graph_builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "sql": "sql",
        "rag": "rag",
        "tools": "tools",
    },
)

graph_builder.add_edge("sql", END)
graph_builder.add_edge("rag", END)
graph_builder.add_edge("tools", END)

support_graph = graph_builder.compile()


def run_support_graph(question: str) -> dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    result = support_graph.invoke({
        "question": question,
        "route": "",
        "answer": "",
        "agent_result": {},
    })
    

    return {
        "question": question,
        "selected_agent": result["route"],
        "answer": result["answer"],
        "agent_result": result["agent_result"],
    }
