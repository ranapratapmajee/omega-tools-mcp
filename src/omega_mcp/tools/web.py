# src/omega_mcp/tools/web.py
from omega_mcp.clients.web_search_client import WebSearchClient
from omega_mcp.core.logger import logger

# Initialize our infrastructure client
search_client = WebSearchClient()

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
    
    # Run the raw lookup
    raw_results = search_client.search(query)
    
    # Handle the empty/error state gracefully for the LLM
    if not raw_results:
        logger.warning(f"No results returned from infrastructure layer for query: '{query}'")
        return f"Search completed, but no relevant web matching results were found for: '{query}'"
        
    # Format the results into a highly structured string optimal for LLM comprehension
    formatted_output = []
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