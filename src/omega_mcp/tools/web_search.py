# filepath: src/omega_mcp/tools/web_search.py
import asyncio
import httpx
from omega_mcp.core.web_search import WebSearchClient
from omega_mcp.logger import logger

_web_client = WebSearchClient()

async def execute_web_search_tool(query: str) -> str:
    """Coordinates the stateless WebSearchClient lifecycle and formats standard XML targets."""
    logger.info(f"🌐 [Web Search] Requesting search index parameters for: '{query}'")
    
    async with httpx.AsyncClient(headers=_web_client.headers, follow_redirects=True) as async_client:
        search_hits = await _web_client.fetch_search_links_async(async_client, query)
        if not search_hits:
            return f"<knowledge_source type='web_search' query='{query}' status='EMPTY'/>"

        tasks = [_web_client.fetch_url_content_async(async_client, hit["url"]) for hit in search_hits]
        try:
            scraped_contents = await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Deep browser scraping hit limits; extracting base snippets.")
            scraped_contents = [""] * len(search_hits)

        xml_blocks = [f"<knowledge_source type='web_search' query='{query}'>"]
        for hit, deep_text in zip(search_hits, scraped_contents):
            body_content = deep_text if (deep_text and len(deep_text) > 100) else hit["snippet"]
            
            xml_blocks.append(
                f"  <record id='{hit['url']}' type='web_page'>\n"
                f"    <specific_fact>{body_content.strip()}</specific_fact>\n"
                f"    <parent_lineage id='{hit['url']}'>{hit['title']}</parent_lineage>\n"
                f"    <semantic_entities>web_index_node</semantic_entities>\n"
                f"  </record>"
            )
        xml_blocks.append("</knowledge_source>")
        return "\n".join(xml_blocks)