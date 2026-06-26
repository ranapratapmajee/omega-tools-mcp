# filepath: src/omega_mcp/tools/web_search.py
from ddgs import DDGS
from omega_mcp.logger import logger
from omega_mcp.config import settings

# =========================================================
# 1. INFRASTRUCTURE LAYER (Standalone API Client)
# =========================================================
class WebSearchClient:
    """
    Infrastructure client for executing internet search queries.
    Encapsulated alongside its tool definition for a flat, clean structure.
    """
    def __init__(self):
        # Gracefully handle dynamic configurations if they exist, else use sensible defaults
        self.max_results = getattr(getattr(settings, 'web', None), 'MAX_RESULTS', 5)
        self.timeout = getattr(getattr(settings, 'app', None), 'NETWORK_TIMEOUT', 10.0)

    def search(self, query: str) -> list[dict]:
        """
        Executes a live search query against DuckDuckGo.
        """
        logger.info(f"Executing web search for query: '{query}'")
        
        try:
            with DDGS(timeout=self.timeout) as ddgs:
                results = ddgs.text(
                    keywords=query,  # Note: python duckduckgo_search uses keywords= parameter
                    max_results=self.max_results
                )
                
                parsed_results = list(results) if results else []
                logger.info(f"Successfully retrieved {len(parsed_results)} search results from live index.")
                return parsed_results
                
        except Exception as e:
            logger.error(f"Search API request failed for query '{query}': {str(e)}")
            return []

# Initialize our single file infrastructure client instance right here
_search_client = WebSearchClient()


# =========================================================
# 2. APPLICATION/PRESENTATION LAYER (MCP Execution Wrapper)
# =========================================================
def search_the_web(query: str) -> str:
    """
    Performs a live web search to retrieve highly accurate, up-to-date information 
    on current events, news, documentation, or generic public data.
    
    Use this tool whenever the user asks questions that require real-time knowledge 
    or details outside your static training data parameters.

    Args:
        query: The optimized search query keywords or question string to submit to the search engine.
    """
    logger.info(f"Tool execution started with query: '{query}'")
    
    # Run the raw lookup via our local client instance
    raw_results = _search_client.search(query)
    
    # Handle the empty/error state gracefully for the LLM context windows
    if not raw_results:
        logger.warning(f"No results returned from infrastructure layer for query: '{query}'")
        return f"Search completed, but no relevant web matching results were found for: '{query}'"
        
    # Format the results into a highly structured string optimal for LLM comprehension
    formatted_output = ["LIVE PUBLIC INTERNET DATA:"]
    for idx, item in enumerate(raw_results, 1):
        title = item.get("title", "Missing Title").strip()
        link = item.get("href", "Missing URL").strip()
        snippet = item.get("body", "No description text provided.").strip()
        
        formatted_output.append(
            f"[{idx}] Title: {title}\n"
            f"    Source URL: {link}\n"
            f"    Content Snippet: {snippet}\n"
            "    ---"
        )
        
    logger.info(f"Tool execution successfully built context payload for {len(raw_results)} results.")
    return "\n\n".join(formatted_output)