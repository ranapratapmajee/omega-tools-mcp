# 🌌 Omega Core Infrastructure Server (Model Context Protocol)

A production-grade, highly decoupled **Model Context Protocol (MCP)** server that acts as a centralized microservice toolkit for LLM agents (Cline, Cursor, Custom Independent Agents, etc.).

Omega is explicitly architected to enforce a strict **Separation of Concerns (SoC)** by separating protocol-agnostic backend service engines from the AI presentation layer. It natively runs as a scalable, containerized **SSE (Server-Sent Events)** network deployment inside Docker on port **`8080`**.

---

## 🏗️ Architectural Layout

The project uses a strict layer separation pattern to guarantee that AI semantic descriptions never bleed into raw infrastructure connectivity modules:

```text
src/omega_mcp/
├── config.py         # Standardized configuration schemas, env variable parsing, and automated boot validations
├── logger.py         # Custom telemetry logging engine directing output safely to sys.stderr
├── server.py         # Central ASGI network routing gateway, tool registry, and lifespan state orchestrator
├── core/             # PROTOCOL-AGNOSTIC DATA ENGINES (Pure Python Data Types Only)
│   ├── service_alpha.py # Foundation engine logic handling connection state pools, file systems, or databases
│   └── service_beta.py  # Standalone service driver handling network adapters, utilities, or external APIs
└── tools/            # SYMMETRICAL PRESENTATION LAYERS (Maps Core Logic to Symmetrical XML)
    ├── tool_alpha.py    # Pulls lifecycle state connections from service_alpha and compiles uniform XML records
    └── tool_beta.py     # Invokes stateless service_beta sequences and converts outputs to standard XML responses

```

### 🛠️ The Symmetrical Presentation Pattern

To completely eliminate **Context Structure Clash**—where an LLM's attention heads accidentally favor one tool pattern or output layout over another—all tools added to this repository must convert core internal records into a uniform, identical XML structural layout (`<knowledge_source>` $\rightarrow$ `<record>`):

```xml
<knowledge_source type="source_type" query="target_query">
  <record id="unique_identifier" score="relevance_weight_if_applicable">
    <specific_fact>Extracted text body content payload goes here...</specific_fact>
    <parent_lineage id="parent_id">Title, Source Reference, or Provenance Metadata Group</parent_lineage>
    <semantic_entities>comma, separated, key, concept, tags</semantic_entities>
  </record>
</knowledge_source>

```

---

## 🧱 System Architecture & Container Data Flow

Omega runs entirely within an isolated Docker container communicating via Server-Sent Events (SSE). This transforms it into a global network tool mesh accessible by local editors and remote agents simultaneously.

```text
  ┌──────────────────────┐      ┌───────────────────────────────┐
  │   VS Code Client     │      │   External Python Agent       │
  │   (Cline / Cursor)   │      │     (Google Gen AI SDK)       │
  └──────────┬───────────┘      └───────────────┬───────────────┘
             │                                  │
             ▼ [HTTP/SSE Network Connection]    ▼ [HTTP POST JSON-RPC]
  ┌─────────────────────────────────────────────────────────────┐
  │                 OMEGA CORE INFRASTRUCTURE SERVER            │
  │                                                             │
  │  ┌───────────┐      ┌─────────────────────────────────────┐ │
  │  │ server.py │ ───> │ tools/tool_alpha.py                 │ │
  │  └─────┬─────┘      │ tools/tool_beta.py                  │ │
  │        │            │ (Symmetrical XML Payload Compilers) │ │
  │        │            └───────────────┬─────────────────────┘ │
  │        ▼ [Lifespan Injection]       │                       │
  │  ┌───────────────────┐              │                       │
  │  │  core/service_*   │◄─────────────┘                       │
  │  └─────────┬─────────┘                                      │
  └────────────┼────────────────────────────────────────────────┘
               │
               ▼ [Network Socket Drivers / API Protocols]
┌───────────────────────────────────────────────────────────────┐
│ Target Infrastructure Layers (Databases, Cloud APIs, Systems) │
└───────────────────────────────────────────────────────────────┘

```

---

## 🐳 Production Deployment via Docker

The project defaults to application-workspace execution mode. Dependencies are managed and synchronized cleanly via `uv` straight inside the container layer.

### 1. Build the Docker Image Locally

```bash
docker build -t omega-mcp .

```

### 2. Configure Your Cluster Engine Layout (`docker-compose.yaml`)

To mount the server into your architecture stack, map external host port **`8080`** to the internal container web gateway port **`8000`**:

```yaml
services:
  omega-mcp:
    image: omega-mcp:latest
    container_name: nexus-tools-mcp
    ports:
      - "8080:8000" # Host Port 8080 -> Container Port 8000
    environment:
      - ENV=production
      - MCP_TRANSPORT=sse
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      
      # Core Service Parameter Allocations
      - SERVICE_ALPHA_URL=http://your-infrastructure-target:port
      - SERVICE_BETA_CREDENTIAL=your_secure_access_token
    restart: unless-stopped

```

Boot up the background microservice network container:

```bash
docker compose up -d

```

---

## 🔌 Connecting to AI Clients

### 1. IDE Client Setup (Cline / VS Code Extension Configuration)

Because the server runs via Docker SSE, your IDE does not need to handle local Python virtual environments or sub-processes. Point your configuration directly to the live SSE network route:

```json
{
  "mcpServers": {
    "omega-tools-docker": {
      "url": "http://localhost:8080/sse"
    }
  }
}

```

### 2. Consuming Tools from Another Project (External Python Agent)

To consume these microservices inside a separate Python service or custom LLM agent framework (e.g., Google Gen AI SDK), call the explicit tool execution paths via HTTP POST requests:

```python
import httpx
from google import genai

ai_client = genai.Client()

def call_mcp_custom_tool(query: str) -> str:
    """Consumes the containerized MCP tool via standard network transport."""
    # FastMCP exposes active tool executions via /tools/{mcp_registered_tool_name}/call
    CONTAINER_URL = "http://localhost:8080/tools/registered_tool_name/call"
    
    try:
        response = httpx.post(CONTAINER_URL, json={"arguments": {"query": query}}, timeout=30.0)
        response.raise_for_status()
        
        # Extract content payload string directly out of standard JSON-RPC schema
        return response.json()["content"][0]["text"]
    except Exception as e:
        return f"<knowledge_source type='custom_tool' status='ERROR' details='{str(e)}'/>"

# Bind directly as a native function tool to your independent agent loop
research_agent = Agent(
    name="ResearchAgent",
    model=ai_client,
    tools=[call_mcp_custom_tool],
    instruction="Execute objective analysis using the provided infrastructure tool endpoint."
)

```

---

## 📈 Scaling Up: Adding New Tools Cleanly

Omega is engineered to expand fluidly. When adding new capabilities, respect the core architectural boundaries by isolating processing routines from interface parsing.

### 🔹 Step 1: Write the Core Domain Logic

Create a protocol-agnostic service module inside `src/omega_mcp/core/` to process your raw metrics or lookups using pure Python types:

```python
# filepath: src/omega_mcp/core/analytics.py
class AnalyticsService:
    async def fetch_metrics(self, target_id: str) -> dict:
        # Pure database lookups, computational algorithms, or external API fetches
        return {"id": target_id, "status": "active", "metrics": [88, 92, 95]}

```

### 🔹 Step 2: Create the Tool Presentation Layer

Create a corresponding interface script inside `src/omega_mcp/tools/` to consume your core engine and map its outputs to the **Symmetrical XML Schema**:

```python
# filepath: src/omega_mcp/tools/analytics_search.py
from omega_mcp.core.analytics import AnalyticsService

_service = AnalyticsService()

async def execute_analytics_tool(target_id: str) -> str:
    data = await _service.fetch_metrics(target_id)
    
    # Compile the uniform symmetrical XML layout for the LLM context window
    return (
        f"<knowledge_source type='custom_analytics' query='{target_id}'>\n"
        f"  <record id='{data['id']}'>\n"
        f"    <specific_fact>Status is {data['status']} with calculated scores.</specific_fact>\n"
        f"    <parent_lineage id='cluster_node'>Internal Operational Cluster</parent_lineage>\n"
        f"    <semantic_entities>{', '.join(map(str, data['metrics']))}</semantic_entities>\n"
        f"  </record>\n"
        f"</knowledge_source>"
    )

```

### 🔹 Step 3: Register the Declarative Route to the Gateway

Open `src/omega_mcp/server.py` and bind your new interface function to the central FastMCP instance using the standard decorators:

```python
# filepath: src/omega_mcp/server.py
from omega_mcp.tools.analytics_search import execute_analytics_tool

@mcp.tool(name="get_custom_metrics", description="Queries internal processing performance metrics.")
async def tool_custom_metrics(target_id: str) -> str:
    return await execute_analytics_tool(target_id)

```

### 🔹 Step 4: Recycle Your Container Stack

Rebuild your Docker container image layers and refresh the cluster setup:

```bash
docker build -t omega-mcp .
docker compose up -d --force-recreate omega-mcp

```

---

## 🔒 Logging & Architecture Guardrails

* **Telemetry Isolation:** High-frequency framework logs from downstream database connection components are suppressed to `WARNING` level inside `server.py` during initialization loops to prevent network telemetry flooding.
* **Stream Defenses:** All logging implementations channel lines to `sys.stderr` safely, keeping container log structures intact while freeing up main transport execution lines.
* **Decoupled Design:** Files created under `core/` have zero dependencies on the `mcp` library package, ensuring that your core infrastructure operations remain clean, reusable, and completely independent of the endpoint framework.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.