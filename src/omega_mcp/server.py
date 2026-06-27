# src/omega_mcp/server.py
from omega_mcp.logger import logger
from mcp.server.fastmcp import FastMCP
from omega_mcp.tools.web_search import search_the_web
from omega_mcp.tools.hybrid_kg_vector_search import execute_hybrid_rsf_graph_rag


# Initialize the central Omega engine
mcp = FastMCP("Omega-MCP-Tools")

# Tools ------------------------------------------------------------------------
@mcp.tool(name="web_search")
async def web_search(query: str) -> str:
    """Executes a live internet query to gather current website contents."""
    return await search_the_web(query)

@mcp.tool(name="hybrid_kg_vector_search")
async def hybrid_kg_vector_search(query: str) -> str:
    """
    Performs a dual-engine semantic vector and full-text keyword search 
    fused via relative scoring algorithms across Neo4j and Chroma DB.
    """
    return await execute_hybrid_rsf_graph_rag(query)

# --------------------------------------------------------------------------------
def main():
    logger.info("Initializing Omega MCP Engine via standard Stdio transport...")
    mcp.run()

if __name__ == "__main__":
    main()