# src/omega_mcp/clients/web_search.py
from ddgs import DDGS
from omega_mcp.core.logger import logger
from omega_mcp.core.config import settings

class WebSearchClient:
    """
    Infrastructure client for executing internet search queries.
    Completely decoupled from the MCP framework logic.
    """
    def __init__(self):
        self.max_results = settings.web.MAX_RESULTS
        self.timeout = settings.app.NETWORK_TIMEOUT

    def search(self, query: str) -> list[dict]:
        """
        Executes a live search query against DuckDuckGo.
        """
        logger.info(f"Executing web search for query: '{query}'")
        
        try:
            with DDGS() as ddgs:
                # 🛠️ Fix: Change keywords= to query=
                results = ddgs.text(
                    query=query, 
                    max_results=self.max_results
                )
                
                parsed_results = list(results) if results else []
                logger.info(f"Successfully retrieved {len(parsed_results)} search results.")
                return parsed_results
                
        except Exception as e:
            logger.error(f"Search API request failed for query '{query}': {str(e)}")
            return []