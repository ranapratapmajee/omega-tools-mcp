# Omega Tools MCP 🌌

A production-grade, highly modular **Model Context Protocol (MCP)** server that acts as a centralized microservice toolkit for LLM agents (Cline, Cursor, Custom Agents, etc.). 

Omega is architected to decouple business logic, external clients, configuration parsing, and semantic AI tool abstractions, allowing you to seamlessly integrate new tools without restructuring your core application footprint. It supports both standard local `stdio` streams and scalable, production-grade `SSE` (Server-Sent Events) network deployment.

---

## 🏗️ Architectural Overview

The project uses a clean infrastructure layer separation pattern:

```text
src/omega_mcp/
├── core/         # Unified system configurations, log pipelines, and constants
├── clients/      # Infrastructure connectors (Pure APIs, Databases, Web Scrapers)
├── tools/        # Semantic AI-facing interfaces decorated with @mcp.tool()
└── server.py     # Central service orchestrator and protocol router

```

### 🛠️ Current Tool Registry

* `omega_web_search`: Live internet search functionality powered by optimized, lightweight web parsers.

---

## 🧱 System Architecture & Data Flow (Production SSE Mode)

In a production environment, Omega runs inside an isolated Docker container communicating via Server-Sent Events (SSE) over HTTP. This decouples it from your IDE and transforms it into a global tool mesh accessible by local editors and remote agents simultaneously.

```text
  ┌──────────────────────┐      ┌───────────────────────────────┐
  │   VS Code Client     │      │   External Python Agent       │
  │   (Cline Panel)      │      │     (Google Gen AI SDK)       │
  └──────────┬───────────┘      └───────────────┬───────────────┘
             │                                  │
             ▼ [HTTP/SSE Network Connection]     ▼ [HTTP POST JSON-RPC]
  ┌─────────────────────────────────────────────────────────────┐
  │                 NEXUS TOOLS MCP (Docker Container)          │
  │                                                             │
  │  ┌───────────┐      ┌───────────────────────────────┐       │
  │  │ server.py │ ───> │ tools/web.py                  │       │
  │  └───────────┘      │ (Semantic AI Function Layer)  │       │
  │                     └───────────────┬───────────────┘       │
  │                                     │                       │
  │                                     ▼                       │
  │                     ┌───────────────────────────────┐       │
  │                     │ clients/web_search_client.py  │       │
  │                     │ (Raw DDGS API Layer)          │       │
  │                     └───────────────┬───────────────┘       │
  └─────────────────────────────────────┼───────────────────────┘
                                        │
                                        ▼ [HTTPS Network Request]
                               ┌─────────────────┐
                               │  DuckDuckGo API │
                               └─────────────────┘

```

---

## 🐳 Production Deployment via Docker

### 1. Build the Docker Image Locally

Run this command inside the `omega-tools-mcp` project directory to lock down your dependencies and build the isolated engine image:

```bash
docker build -t omega-mcp .

```

### 2. Integrate with Your Multi-Container Stack (`docker-compose.yml`)

To add this tool hub to your primary agent project stack (alongside ChromaDB, Neo4j, etc.), map it into your orchestration layout using port **`8080`** to avoid port collisions with your vector databases:

```yaml
services:
  omega-mcp:
    image: omega-mcp
    container_name: nexus-tools-mcp
    ports:
      - "8080:8000" # Maps host Mac port 8080 to container internal port 8000
    environment:
      - OMEGA_ENV=production
      - OMEGA_SEARCH_MAX_RESULTS=5
    restart: unless-stopped
    depends_on:
      - redis

```

Boot the entire ecosystem container grid together:

```bash
docker compose up -d

```

---

## 🔌 Connecting to AI Clients

### 1. IDE Client Setup (Cline / VS Code Extension)

Once the Docker stack is active on port `8080`, your IDE does not need to manage local Python runtime subprocesses. Simply swap your configuration profile inside `cline_mcp_settings.json` to look up the live web endpoint:

```json
{
  "mcpServers": {
    "omega-tools-docker": {
      "url": "http://localhost:8080/sse"
    }
  }
}

```

### 2. External Project Integration (Google Gen AI SDK Agent)

To consume this microservice inside an independent custom Python Agent framework without writing complex setup commands or parameter duplications, define a clean HTTP network pass-through function:

```python
import httpx
from google import genai

ai_client = genai.Client()

def web_search(query: str) -> str:
    """
    Executes a web search by sending an HTTP POST directly to the containerized microservice.
    """
    CONTAINER_URL = "http://localhost:8080/tools/omega_web_search/call"
    try:
        response = httpx.post(
            CONTAINER_URL, 
            json={"arguments": {"query": query}},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"Tool Error: Could not reach container server. Details: {str(e)}"

# Register straight to your Agent tool array
research_agent = Agent(
    name="ResearchAgent",
    model=ai_client,
    tools=[graph_rag_retrieval, web_search],
    instruction="Your system compliance laws here..."
)

```

---

## 🚀 Local Development (Non-Docker Setup)

### 1. Cline (VS Code Extension)

Open your global `cline_mcp_settings.json` and append the server into your configuration schema:

```json
{
  "mcpServers": {
    "omega-tools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/omega-tools-mcp",
        "run",
        "src/omega_mcp/server.py"
      ],
      "env": {
        "OMEGA_SEARCH_MAX_RESULTS": "5",
        "OMEGA_ENV": "dev"
      }
    }
  }
}

```

### 2. Cursor or Windsurf

Navigate to **Settings -> Features -> MCP**, click **+ Add New MCP Server**, select `command` mode, and set the invocation signature to:

```bash
uv --directory /absolute/path/to/your/omega-tools-mcp run omega-tools

```

### Prerequisites

This project relies on `uv` for lightning-fast environment isolation. Install it on macOS using:

```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

```


### Setup & Diagnostic Verification

1. Synchronize your virtual environment:

```bash
uv sync

```

2. Run the standalone diagnostic validation check script:

```bash
PYTHONPATH=src uv run tests/test_search.py

```

---

## 📈 Scaling Up: Adding More Tools

Omega is built to expand gracefully. To introduce a new tool domain (e.g., database queries or file synchronization actions):

1. **Add Configuration Properties**: Declare environment variables inside `src/omega_mcp/core/config.py`.
2. **Build the Infrastructure Core**: Write the pure functional driver code inside `src/omega_mcp/clients/`.
3. **Draft Semantic Descriptions**: Create the interface under `src/omega_mcp/tools/` documenting parameters clearly in the docstrings so the LLM understands when to call it.
4. **Link to Orchestration Registry**: Anchor it to the service endpoint inside `src/omega_mcp/server.py`:
```python
from omega_mcp.tools.new_module import execute_action
mcp.tool(name="omega_new_action")(execute_action)

```



---

## 🔒 Security & Logging Guardrails

* **Stdout Safety**: Standard `print()` streams interfere with JSON-RPC. All telemetry or debug trace tracking must use the custom logger `omega_mcp.core.logger` routing pipeline, which channels output strictly to `sys.stderr`.
* **Layer Isolation**: Keep AI-specific framework concepts out of the `clients/` folder to ensure your infrastructure layers remain simple and testable independently.
