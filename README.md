# SupportIQ --- Cloud-Native Multi-Agent AI Customer Support System

SupportIQ is a multi-agent customer-support application built with
**FastAPI, LangGraph, PostgreSQL, ChromaDB, Groq, React, and Docker
Compose**. A supervisor routes each incoming question to the most
suitable agent: SQL for structured customer/order data, RAG for
support-policy knowledge, or tools for supported lookups.

## Features

-   **LangGraph supervisor** routes requests to the SQL, RAG, or tools
    agent.
-   **SQL agent** answers questions using structured PostgreSQL data.
    Queries are restricted to read-only operations and allowed tables.
-   **RAG agent** retrieves relevant information from the support
    knowledge base, including shipping and refund policies, using
    ChromaDB.
-   **Tool agent** supports lookups such as order tracking and customer
    support tickets.
-   **FastAPI backend** exposes API endpoints for health checks and
    agent interactions.
-   **React + Vite frontend** provides a chat interface with Markdown
    rendering and conversation history saved in the browser.
-   **Docker Compose** runs the application services locally.

## Technology Stack

  -----------------------------------------------------------------------
  Layer                               Technologies
  ----------------------------------- -----------------------------------
  Frontend                            React, Vite, JavaScript, CSS,
                                      `react-markdown`, `remark-gfm`

  Backend                             Python, FastAPI, Uvicorn

  Agent orchestration                 LangGraph

  Language model                      Groq API

  Structured data                     PostgreSQL

  Knowledge retrieval                 ChromaDB

  Containerization                    Docker, Docker Compose

  Testing                             pytest
  -----------------------------------------------------------------------

## Architecture

``` text
React + Vite frontend
        |
        | HTTP requests
        v
FastAPI backend
        |
        v
LangGraph supervisor
   |        |        |
   v        v        v
 SQL agent  RAG agent  Tool agent
   |        |        |
PostgreSQL ChromaDB  Order/ticket lookups
```

## Project Structure

``` text
customer-support-ai/
├── app/
│   ├── agents/            # SQL, RAG, and tool agents
│   ├── db/                # Database initialization and related code
│   ├── main.py             # FastAPI application and endpoints
│   └── ...                 # Graph orchestration and supporting modules
├── data/
│   └── knowledge_base/     # Support policy documents for retrieval
├── frontend/               # React + Vite user interface
├── tests/                  # Automated tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

Install the following before running the project:

-   Docker Desktop
-   Node.js and npm (for running the frontend outside Docker)
-   A Groq API key

## Configuration

Create a local `.env` file from the example:

``` bash
cp .env.example .env
```

Edit `.env` and set the values required by your local configuration,
including your Groq API key and database settings. Use the variable
names and service settings documented in `.env.example` and
`docker-compose.yml`.

**Security:** Never commit `.env` or publish API keys, database
passwords, or other credentials. Only commit `.env.example` with
placeholder values.

## Run with Docker Compose

From the project root:

``` bash
docker compose up --build
```

When the services are running, the API is expected at:

-   API root: `http://localhost:8000/`
-   Health check: `http://localhost:8000/health`
-   API documentation: `http://localhost:8000/docs`

The frontend can be run separately during development.

## Run the Frontend

In a second terminal:

``` bash
cd frontend
npm install
npm install react-markdown remark-gfm lucide-react
npm run dev
```

Open the local URL printed by Vite (commonly `http://localhost:5173`; if
that port is busy, Vite may choose another port).

The frontend API URL must point to the backend address. For local
development, that is typically `http://localhost:8000`.

## API Endpoints

The backend includes endpoints for:

  -----------------------------------------------------------------------
  Endpoint                            Purpose
  ----------------------------------- -----------------------------------
  `GET /`                             API root

  `GET /health`                       Basic health check

  `GET /health/database`              Database health check

  `GET /orders/{tracking_number}`     Order lookup

  `POST /agent/sql`                   Query structured data through the
                                      SQL agent

  `POST /agent/rag`                   Retrieve support-policy information

  `POST /agent/tools`                 Run supported support tools

  `POST /agent/support`               Route a support question through
                                      the supervisor
  -----------------------------------------------------------------------

Check `http://localhost:8000/docs` for the current request and response
schemas.

## Run Tests

Run the test suite inside the running API container:

``` bash
docker compose exec -e PYTHONPATH=/app api python -m pytest -v /app/tests
```

## Current Scope and Deployment Notes

-   Conversation history in the frontend is stored in the current
    browser using local storage; it is not shared across browsers or
    users.
-   Local Docker Compose configuration is intended for development.
    Deploying publicly requires configuring each service, environment
    variables, persistent storage where needed, and the frontend's
    production API URL.
-   Keep the SQL agent's database credentials read-only and do not
    expose secrets in the repository.

## Future Improvements

-   Persist conversation history in PostgreSQL and associate it with
    authenticated users.
-   Add user authentication and role-based access.
-   Add human handoff and ticket creation workflows.
-   Add observability, structured logs, and evaluation for agent routing
    and response quality.
-   Deploy the frontend and backend with managed services and production
    environment variables.

## License

No license has been specified yet. Add a license file if you intend to
define how others may use, modify, and distribute this project.
