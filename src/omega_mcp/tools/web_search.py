# filepath: src/omega_mcp/tools/web.py
import asyncio
import logging
from urllib.parse import urlparse, urlunparse
import httpx
from bs4 import BeautifulSoup
from omega_mcp.logger import logger
from omega_mcp.config import settings

# Silence background HTTP connection network logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# =========================================================
# 1. INFRASTRUCTURE LAYER (API Queries + Parallel Scrapers)
# =========================================================
class WebSearchClient:
    """
    High-speed, zero-junk concurrent web search and webpage text scrapper client.
    """
    def __init__(self):
        self.endpoint = "https://html.duckduckgo.com/html/"
        self.max_results = getattr(getattr(settings, 'web', None), 'MAX_RESULTS', 3)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.ad_blacklist = ["duckduckgo.com/y.js", "click", "doubleclick", "adservice", "googleadservices", "bing.com/aclick"]

    def clean_and_normalize_url(self, raw_url: str) -> str | None:
        """Strips out analytics tracking arrays, ad routers, and deep query bloat."""
        if not raw_url:
            return None
            
        if any(token in raw_url.lower() for token in self.ad_blacklist):
            return None

        try:
            parsed = urlparse(raw_url)
            clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
            return clean_url if parsed.netloc else None
        except Exception:
            return None

    def fetch_search_links(self, query: str) -> list[dict]:
        """Scrapes DuckDuckGo HTML structurally to extract valid landing targets."""
        if not query or not query.strip():
            return []
        
        try:
            with httpx.Client(timeout=8.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.post(self.endpoint, data={"q": query})
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            logger.debug(f"Search engine index lookup connection failure: {e}")
            return []

        results = []
        soup = BeautifulSoup(html, "html.parser")
        
        for result in soup.select(".result"):
            if len(results) >= self.max_results:
                break
            
            link_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            
            raw_href = " ".join((link_el.get("href", "") if link_el else "").split()).strip()
            clean_href = self.clean_and_normalize_url(raw_href)
            
            if not clean_href:
                continue

            title = " ".join((link_el.get_text(" ", strip=True) if link_el else "").split()).strip()
            snippet = " ".join((snippet_el.get_text(" ", strip=True) if snippet_el else "").split()).strip()
            
            results.append({
                "title": title or "Source Profile",
                "href": clean_href,
                "snippet_fallback": snippet
            })
            
        return results

    async def fetch_url_content_async(self, client: httpx.AsyncClient, url: str, max_chars: int = 2500) -> str:
        """Asynchronously extracts webpage main content with an active timeout wrapper."""
        try:
            resp = await client.get(url, timeout=4.0)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.debug(f"Unable to resolve deep content for {url} | Reason: {e}")
            return ""

        try:
            import trafilatura
            extracted = trafilatura.extract(html) or ""
        except Exception:
            extracted = ""

        if not extracted:
            try:
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg", "form"]):
                    tag.decompose()
                extracted = soup.get_text(" ", strip=True)
            except Exception:
                return ""

        clean = " ".join((extracted or "").split()).strip()
        return f"{clean[:max_chars]}..." if len(clean) > max_chars else clean


_web_client = WebSearchClient()


# =========================================================
# 2. APPLICATION/PRESENTATION LAYER (Standardized XML payload)
# =========================================================
async def search_the_web(query: str) -> str:
    """
    Executes a high-efficiency internet search query, filtering out tracking 
    junk and fetching deep-scraped content concurrently under a safe time-out window.
    """
    logger.info(f"🌐 [MCP Web Search] Querying active internet for: '{query}'")
    
    search_hits = _web_client.fetch_search_links(query)
    if not search_hits:
        return f"<knowledge_source type='web' status='EMPTY' query='{query}'/>"

    # Standardized XML block layout mirroring your GraphRAG tool output exactly
    compiled_output = [f"## LIVE PUBLIC INTERNET RETRIEVAL PACKET\n<knowledge_source type='web' query='{query}'>"]
    
    async with httpx.AsyncClient(headers=_web_client.headers, follow_redirects=True) as async_client:
        tasks = [_web_client.fetch_url_content_async(async_client, hit["href"]) for hit in search_hits]
        
        try:
            scraped_contents = await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)
        except asyncio.TimeoutError:
            logger.debug("Concurrent scraping task pool reached execution limits, using fast-snippets fallback.")
            scraped_contents = [""] * len(search_hits)

        for hit, deep_text in zip(search_hits, scraped_contents):
            title = hit["title"]
            url = hit["href"]
            
            # Choose the maximum density data block available
            content_payload = deep_text if (deep_text and len(deep_text) > 100) else hit["snippet_fallback"]
            content_payload = content_payload.strip()

            # Symmetric token layout mapping matches your vector node variables
            item_payload = (
                f"  <record id='{url}' type='web_scrape'>\n"
                f"    <specific_fact>{content_payload}</specific_fact>\n"
                f"    <parent_lineage id='{url}'>{title}</parent_lineage>\n"
                f"    <semantic_entities>[]</semantic_entities>\n"
                f"  </record>"
            )
            compiled_output.append(item_payload)
                
    compiled_output.append("</knowledge_source>")
    return "\n".join(compiled_output)