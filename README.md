# 🌌 Omega Tools MCP (Model Context Protocol Server)

A production-grade, highly modular **Model Context Protocol (MCP)** server that acts as a centralized microservice toolkit for LLM agents (Cline, Cursor, Custom Independent Agents, etc.).

Omega is explicitly architected to decouple business logic, external infrastructure client hooks, configuration parsing, and semantic AI tool abstractions—allowing you to seamlessly integrate new capabilities without restructuring your core application footprint. It natively supports both local `stdio` streams for IDEs and scalable, production-grade `SSE` (Server-Sent Events) network deployments.

---

## 🏗️ Architectural Overview

The project uses a clean infrastructure layer separation pattern to guarantee that AI semantic descriptions never bleed into raw connectivity modules:

```text
src/omega_mcp/
├── config.py     # Unified dataclass configuration schemas, env variables, and validations
├── logger.py     # Custom telemetry logging engine directing tracking output safely to sys.stderr
├── server.py     # Central service orchestrator, protocol router, and FastMCP instance
└── tools/        # Symmetrical XML-structured AI-facing interfaces decorated with @mcp.tool()

```

### 🛠️ Core Symmetrical Tool Registry Blueprint

To eliminate the **Context Structure Clash** where an LLM's internal attention mechanism favors one tool type over another, all tools added to this repository must return data encapsulated in identical, uniform XML schemas (`<knowledge_source>` $\rightarrow$ `<record>`):

* **`omega_tool_alpha`**: Generic placeholder for your first backend infrastructure service tool (e.g., Database, Vector, or File Synchronization lookup).
* **`omega_tool_beta`**: Generic placeholder for your second external connectivity service tool (e.g., API scrapers, code execution rtimes, or network clients).

---

## 🧱 System Architecture & Data Flow (Production SSE Mode)

In a production environment, Omega runs inside an isolated Docker container communicating via Server-Sent Events (SSE) over HTTP. This decouples it from your workspace runtime and transforms it into a global tool mesh accessible by local editors and remote agents simultaneously.

```text
  ┌──────────────────────┐      ┌───────────────────────────────┐
  │   VS Code Client     │      │   External Python Agent       │
  │   (Cline / Cursor)   │      │     (Google Gen AI SDK)       │
  └──────────┬───────────┘      └───────────────┬───────────────┘
             │                                  │
             ▼ [HTTP/SSE Network Connection]     ▼ [HTTP POST JSON-RPC]
  ┌─────────────────────────────────────────────────────────────┐
  │                 NEXUS TOOLS MCP (Docker Container)          │
  │                                                             │
  │  ┌───────────┐      ┌─────────────────────────────────────┐ │
  │  │ server.py │ ───> │ tools/omega_tool_alpha.py           │ │
  │  └───────────┘      │ tools/omega_tool_beta.py            │ │
  │                     │ (Symmetrical XML Payload Layer)     │ │
  │                     └───────────────┬─────────────────────┘ │
  └─────────────────────────────────────┼───────────────────────┘
                                        │
                       ┌────────────────┴────────────────┐
                       ▼ [Network Socket Drivers]        ▼ [External API Call]
              ┌─────────────────────────────────┐      ┌─────────────────┐
              │ Local Infrastructure Clusters   │      │  External Cloud │
              │ (Databases, Servers, Backends)  │      │  Service / APIs │
              └─────────────────────────────────┘      └─────────────────┘

```

---

## 🐳 Production Deployment via Docker

### 1. Build the Docker Image Locally

Run this command inside the project root directory to lock down your dependencies and build the isolated engine image:

```bash
docker build -t omega-mcp .

```

### 2. Integrate with Your Multi-Container Stack (`docker-compose.yaml`)

To add this tool hub to your primary agent project stack, map it into your orchestration layout using port **`8080`** to avoid port collisions with other core database instances:

```yaml
services:
  omega-mcp:
    image: omega-mcp
    container_name: nexus-tools-mcp
    ports:
      - "8080:8000" # Maps host Mac port 8080 to container internal port 8000
    environment:
      - OMEGA_ENV=production
      # Global environment fallbacks for your downstream tool logic
      - TOOL_ALPHA_PARAM=value
      - TOOL_BETA_PARAM=value
    restart: unless-stopped

```

Boot the entire ecosystem container grid together:

```bash
docker compose up -d

```

---

## 🔌 Connecting to AI Clients

### 1. IDE Client Setup (Cline / VS Code Extension)

Once the Docker stack is active on port `8080`, your IDE does not need to manage local Python runtime subprocesses. Simply swap your configuration profile inside `cline_mcp_settings.json` to point directly to the live Server-Sent Events endpoint:

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

To consume these microservices inside an independent custom Python Agent framework without writing complex setup commands or parameter duplications, define clean HTTP network pass-through functions matching the symmetrical schemas:

```python
import httpx
from google import genai

ai_client = genai.Client()

def call_mcp_tool_alpha(query: str) -> str:
    CONTAINER_URL = "http://localhost:8080/tools/omega_tool_alpha/call"
    try:
        response = httpx.post(CONTAINER_URL, json={"arguments": {"query": query}}, timeout=30.0)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"<knowledge_source type='alpha' status='ERROR' details='{str(e)}'/>"

def call_mcp_tool_beta(query: str) -> str:
    CONTAINER_URL = "http://localhost:8080/tools/omega_tool_beta/call"
    try:
        response = httpx.post(CONTAINER_URL, json={"arguments": {"query": query}}, timeout=30.0)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"<knowledge_source type='beta' status='ERROR' details='{str(e)}'/>"

# Register straight to your orchestrator's tool array
research_agent = Agent(
    name="ResearchAgent",
    model=ai_client,
    tools=[call_mcp_tool_alpha, call_mcp_tool_beta],
    instruction="Your system compliance laws here..."
)

```

---

## 🚀 Local Development (Non-Docker Setup)

### Prerequisites

This project relies on `uv` for lightning-fast environment isolation and virtual runtime tracking. Install it on macOS using:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

```

### Setup & Diagnostic Verification

1. Synchronize your local virtual environment:

```bash
uv sync

```

2. Run your verification test suite to check end-to-end component functionality:

```bash
PYTHONPATH=src uv run tests/test_search.py

```

### 1. Cline Config (VS Code Extension Stdio Mode)

Open your global `cline_mcp_settings.json` and append the server using absolute MacBook paths to trigger standard stdio transport streams:

```json
{
  "mcpServers": {
    "omega-tools-stdio": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/your/omega-tools-mcp",
        "run",
        "src/omega_mcp/server.py"
      ],
      "env": {
        "OMEGA_ENV": "dev",
        "TOOL_ALPHA_PARAM": "value",
        "TOOL_BETA_PARAM": "value"
      }
    }
  }
}

```

### 2. Cursor or Windsurf

Navigate to **Settings -> Features -> MCP**, click **+ Add New MCP Server**, select `command` mode, and configure the invocation signature:

```bash
uv --directory /absolute/path/to/your/omega-tools-mcp run src/omega_mcp/server.py

```

---

## 📈 Scaling Up: Adding New Tools & Sets

Omega is engineered to expand gracefully. To maintain perfect token weight optimization across your downstream agent loops, all new tool additions must adhere to the **Symmetrical XML Presentation Schema**.

### 🔹 Step 1: Draft the Symmetrical Tool File

Create your new tool file inside `src/omega_mcp/tools/your_custom_tool.py`. Use descriptive function docstrings so the agent can accurately map parameters during execution turns:

```python
# filepath: src/omega_mcp/tools/your_custom_tool.py
import logging
from omega_mcp.logger import logger

async def execute_custom_tool(query: str) -> str:
    """
    Executes an optimized, low-latency target action using specified parameters.
    
    Args:
        query (str): The search phrase or identifier target to analyze.
    """
    # 🛰️ Telemetry Tracker: Output single line status metrics to keep terminal quiet
    logger.info(f"⚙️ [MCP Tool Action] Running custom tool node execution for: '{query}'")
    
    # ... Your background infrastructure client or API logic goes here ...
    extracted_body_content = "Target payload data resolved."
    parent_or_source_origin = "CLUSTER-01"
    title_or_provenance = "System Diagnostics Log Block"
    metadata_list_or_tags = "[TAG_A, TAG_B]"
    
    # 🪐 ALWAYS wrap your final presentation return payload inside this standard XML schema layout
    return (
        f"## CAPTURED RAW SYSTEM INSIGHTS\n"
        f"<knowledge_source type='custom_action' query='{query}'>\n"
        f"  <record id='{parent_or_source_origin}' type='system_telemetry'>\n"
        f"    <specific_fact>{extracted_body_content}</specific_fact>\n"
        f"    <parent_lineage id='{parent_or_source_origin}'>{title_or_provenance}</parent_lineage>\n"
        f"    <semantic_entities>{metadata_list_or_tags}</semantic_entities>\n"
        f"  </record>\n"
        f"</knowledge_source>"
    )

```

---

### 🔹 Step 2: Register the Tool Node to the Server

Open `src/omega_mcp/server.py` and register your new decorated endpoint block to the FastMCP initialization engine:

```python
# filepath: src/omega_mcp/server.py
# 1. Append your import hook at the top
from omega_mcp.tools.your_custom_tool import execute_custom_tool

# 2. Bind the tool function directly to the mcp instance wrapper below the other tool definitions
mcp.tool(name="omega_custom_tool")(execute_custom_tool)

```

---

### 🔹 Step 3: Choose Your Development Deployment Strategy

#### 🚀 Subsection A: Local Development & Verification (Without Docker via `uv`)

If you are developing locally on your MacBook workspace, follow this workflow loop to verify your newly added tool without container overhead:

1. **Verify Your Environment Syntax:** Ensure any required system libraries are updated inside `pyproject.toml`.
2. **Execute Your Functional Test Suite:** Draft or update your verification script inside the `tests/` directory to query your new method directly, then execute it via `uv`:
```bash
PYTHONPATH=src uv run python tests/test_custom_tool.py

```


3. **Validate Local Transport Communication:** Run the server inside your active shell manually to check if it compiles your new function into the protocol schema smoothly without throwing syntax errors:
```bash
uv run src/omega_mcp/server.py

```


4. **Hot-Reload Connection Check:** If you are using Cline or Cursor, restart the active MCP server thread within your editor interface panel. Your model will instantly locate the newly registered `omega_custom_tool` option inside its active schema registry window!

#### 🐳 Subsection B: Isolated Container Cluster Deployment (With Docker)

If you are scaling out your application or integrating this node with a production-grade multi-container cluster grid, follow this environment setup pattern:

1. **Rebuild the Local Base Layer Image:** Run a targeted layer cache build command within the repository root to compile your added Python files into the isolated file matrix:
```bash
docker build -t omega-mcp .

```


2. **Expose Custom Runtime Environment Variables:** If your new tool requires connection strings, API keys, or database endpoint pointers, map them directly into your host architecture `docker-compose.yaml` configuration file:
```yaml
# append under your omega-mcp configuration segment matrix
environment:
  - OMEGA_ENV=production
  - CUSTOM_TOOL_SECRET_KEY=your_secure_credential_token
  - TARGET_BACKEND_CLUSTER_URL=http://your-internal-network-node:9000

```


3. **Restart the Stack Execution Container Grid:** Issue a force-recreate call to recycle the active tool microservice nodes seamlessly in the background:
```bash
docker compose up -d --force-recreate omega-mcp

```


4. **Audit Live Network Event Health:** Inspect your container runtime telemetry logs to ensure your tool engine successfully hooks into your upstream APIs without dropping connectivity packets:
```bash
docker logs -f nexus-tools-mcp

```



---

## 🔒 Security & Logging Guardrails

* **Stdout Safety Regulation**: Standard Python `print()` statements output to `sys.stdout`, which corrupts the JSON-RPC communication stream over stdio and crashes the active AI client session. All telemetry tracking, debug logs, and network connection tracing must use `omega_mcp.logger.logger` which securely channels lines to `sys.stderr`.
* **Telemetry Suppression**: Background connection logs from heavy external framework clients are explicitly overwritten to `WARNING` at runtime inside `server.py` to prevent the console logs from flooding during sequential lookups.
* **Clean Layer Isolation**: Keep server-specific framework properties completely decoupled from raw backend extraction drivers. The scripts in `tools/` handle presentation data wrapping, keeping your background infrastructure modules independently testable.
