# src/omega_mcp/server.py
from mcp.server.fastmcp import FastMCP
from omega_mcp.tools.web import search_the_web
from omega_mcp.core.logger import logger

# Initialize the central Omega engine
mcp = FastMCP("Omega-MCP-Tools")

# Tools
@mcp.tool(name="web_search")
def web_search(query: str) -> str:
    """Executes a live internet query to gather current website contents."""
    return search_the_web(query)

def main():
    logger.info("Initializing Omega MCP Engine via standard Stdio transport...")
    mcp.run()

if __name__ == "__main__":
    main()