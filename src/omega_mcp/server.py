# src/omega_mcp/server.py
from mcp.server.fastmcp import FastMCP
from omega_mcp.tools.web import search_the_web
from omega_mcp.core.logger import logger

# 1. Initialize the central Omega engine
mcp = FastMCP("Omega-Universal-Tools")

# 2. Register our web search tool
mcp.tool(name="omega_web_search")(search_the_web)

def main():
    logger.info("Initializing Omega MCP Engine via standard Stdio transport...")
    mcp.run()

if __name__ == "__main__":
    main()