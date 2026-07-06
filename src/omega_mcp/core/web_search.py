# filepath: src/omega_mcp/core/web_search.py
import logging
import httpx
from bs4 import BeautifulSoup
from omega_mcp.logger import logger
from omega_mcp.config import settings

logging.getLogger("httpx").setLevel(logging.WARNING)

class WebSearchClient:
    """Core network client driving raw external web scraper integrations."""
    def __init__(self):
        self.endpoint = "https://html.duckduckgo.com/html/"
        self.max_results = getattr(getattr(settings, 'web', None), 'MAX_RESULTS', 3)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.ad_blacklist = ["duckduckgo.com/y.js", "click", "doubleclick", "adservice", "googleadservices", "bing.com/aclick"]

    def clean_and_normalize_url(self, raw_url: str) -> str | None:
        if not raw_url or any(token in raw_url.lower() for token in self.ad_blacklist):
            return None
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(raw_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", "")) if parsed.netloc else None
        except Exception:
            return None

    async def fetch_search_links_async(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        try:
            resp = await client.post(self.endpoint, data={"q": query}, timeout=6.0)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.debug(f"Search index failure: {e}")
            return []

        results = []
        soup = BeautifulSoup(html, "html.parser")
        for result in soup.select(".result"):
            if len(results) >= self.max_results:
                break
            link_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            
            clean_href = self.clean_and_normalize_url(" ".join((link_el.get("href", "") if link_el else "").split()).strip())
            if not clean_href:
                continue

            results.append({
                "title": " ".join((link_el.get_text(" ", strip=True) if link_el else "").split()).strip() or "Source",
                "url": clean_href,
                "snippet": " ".join((snippet_el.get_text(" ", strip=True) if snippet_el else "").split()).strip()
            })
        return results

    async def fetch_url_content_async(self, client: httpx.AsyncClient, url: str, max_chars: int = 2500) -> str:
        try:
            resp = await client.get(url, timeout=4.0)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.debug(f"Content scrape timeout/failure for {url}: {e}")
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