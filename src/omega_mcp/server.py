# filepath: src/omega_mcp/server.py
import os
import sys
import logging
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context

# Core Engines and Services
from omega_mcp.core.graph_rag import GraphRagService

# Decoupled Presenter Tools
from omega_mcp.tools.web_search import execute_web_search_tool
from omega_mcp.tools.graph_search import execute_graph_search_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
server_logger = logging.getLogger("omega_mcp_server")
logging.getLogger("httpx").setLevel(logging.WARNING)

mcp = FastMCP("Omega Core Infrastructure Server")

@asynccontextmanager
async def server_lifespan(server):
    """Initializes and recycles global core infrastructure connection instances."""
    try:
        service = GraphRagService()
        # FIX: Map straight to server.app_state or use the generic dictionary container state 
        # to ensure it is globally accessible across concurrent SSE network loops.
        server.app_state["graph_rag_service"] = service
        server_logger.info("🚀 Lifespan Setup: Instantiated and attached GraphRagService cluster pool.")
    except Exception as e:
        server.app_state["graph_rag_service"] = None
        server_logger.error(f"❌ Lifespan Setup: Bypassed GraphRagService resource injection: {e}")
        
    yield
    
    # Teardown Sequence
    service = server.app_state.get("graph_rag_service")
    if service and hasattr(service, "neo4j_driver"):
        await service.neo4j_driver.close()
        server_logger.info("🔒 Lifespan Teardown: Disposed connection resources safely.")

mcp.set_lifespan(server_lifespan)

# ===========================================================================
# TOOL LAYER ROUTERS
# ===========================================================================

@mcp.tool(name="search_the_web", description="Queries live internet for real-time contextual data updates.")
async def tool_web_search(query: str) -> str:
    return await execute_web_search_tool(query)

@mcp.tool(name="hybrid_graph_vector_search", description="Queries internal secure vector-graph Knowledge Bases.")
async def tool_graph_search(query: str, ctx: Context) -> str:
    return await execute_graph_search_tool(query, ctx)

# ===========================================================================
# MULTI-MODE TRANSPORT INITIALIZATION ENTRYPOINT
# ===========================================================================
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse").lower()
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    if transport == "sse":
        server_logger.info(f"✨ Spawning production network cluster SSE stack on http://{host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "stdio":
        server_logger.info("⚡ Spawning local standard stream subprocess channels")
        mcp.run(transport="stdio")
    else:
        server_logger.error(f"❌ Deployment Aborted: Invalid configuration target '{transport}'")
        sys.exit(1)