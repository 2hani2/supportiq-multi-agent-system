
import os

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from app.tools.customer_tools import (
    lookup_order,
    lookup_customer_tickets,
)


@tool
def order_lookup_tool(tracking_number: str) -> dict:
    """Look up an order using its exact tracking number, such as TRK1001."""
    return lookup_order(tracking_number)


@tool
def customer_ticket_lookup_tool(customer_name: str) -> dict:
    """Find support tickets for a customer using their full name."""
    return lookup_customer_tickets(customer_name)


tools = [
    order_lookup_tool,
    customer_ticket_lookup_tool,
]

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"],
)

llm_with_tools = llm.bind_tools(tools)


def run_tool_agent(question: str) -> dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    messages = [
        SystemMessage(
            content=(
                "You are a customer support assistant. "
                "Use the available tools to look up order or support-ticket "
                "information when needed. Never invent database results. "
                "Only report information returned by the tools. "
                "If the customer hasn't provided enough information to use "
                "a tool, ask for the missing information."
            )
        ),
        HumanMessage(content=question),
    ]

    response = llm_with_tools.invoke(messages)
    tool_results = []

    # Allow the model to make a tool call, receive the result,
    # and produce a final answer.
    for _ in range(5):
        if not response.tool_calls:
            break

        messages.append(response)

        for tool_call in response.tool_calls:
            selected_tool = next(
                (
                    item for item in tools
                    if item.name == tool_call["name"]
                ),
                None,
            )

            if selected_tool is None:
                result = {"error": "Unknown tool requested."}
            else:
                try:
                    result = selected_tool.invoke(tool_call["args"])
                except Exception:
                    result = {
                        "error": "The requested lookup failed."
                    }

            tool_results.append({
                "tool": tool_call["name"],
                "result": result,
            })

            from langchain_core.messages import ToolMessage

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )

        response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        answer = (
            "I couldn't complete the lookup within the allowed "
            "number of tool calls. Please try again."
        )
    else:
        answer = response.content

    return {
        "question": question,
        "answer": answer,
        "tool_results": tool_results,
    }
