# filepath: src/omega_mcp/core/graph_rag.py
import logging
import httpx
from neo4j import AsyncGraphDatabase
import chromadb
from chromadb.config import Settings as ChromaSettings
from omega_mcp.logger import logger
from omega_mcp.config import settings

logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

class GraphRagService:
    """Core domain engine managing internal vector-graph retrieval pools."""
    def __init__(self):
        self.neo4j_uri = settings.db.NEO4J_URI
        self.neo4j_user = settings.db.NEO4J_USER
        self.neo4j_password = settings.db.NEO4J_PASSWORD
        
        self.chroma_host = settings.db.CHROMA_HOST
        self.chroma_port = settings.db.CHROMA_PORT
        self.chroma_collection = settings.db.CHROMA_COLLECTION
        self.embedding_url = f"{settings.db.LOCAL_LLM_URL}/api/embeddings"
        self.model_name = settings.db.EMBEDDING_MODEL
        
        self.neo4j_driver = AsyncGraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        self.chroma_client = chromadb.HttpClient(
            host=self.chroma_host, 
            port=self.chroma_port,
            settings=ChromaSettings(chroma_api_impl="chromadb.api.fastapi.FastAPI", persist_directory=None)
        )

    async def _generate_embedding_async(self, client: httpx.AsyncClient, text_content: str) -> list:
        try:
            resp = await client.post(self.embedding_url, json={"model": self.model_name, "prompt": text_content}, timeout=5.0)
            resp.raise_for_status()
            return resp.json().get("embedding", [])
        except Exception:
            return []

    async def execute_search(self, query: str, top_k: int = 3) -> list[dict]:
        """Queries databases and yields clean, schema-free internal Python dicts."""
        async with httpx.AsyncClient() as http_client:
            raw_payload = await self._hybrid_search_logic(http_client, query, top_k)
            
        sorted_chunks = raw_payload.get("sorted_chunks", [])
        record_map = raw_payload.get("lineage_records", {})
        chunk_text_cache = raw_payload.get("text_cache", {})

        output_records = []
        seen_parent_ids = set()

        for chunk_id, combined_score in sorted_chunks:
            child_text = chunk_text_cache.get(chunk_id, "").strip()
            record = record_map.get(chunk_id)
            
            parent_id, parent_text = None, None
            if record:
                parent_id = str(record.get("parent_id") or "").strip() or None
                if parent_id:
                    if parent_id not in seen_parent_ids:
                        seen_parent_ids.add(parent_id)
                        parent_text = str(record.get("parent_text") or "").strip() or None
                    else:
                        parent_text = f"[OMITTED_DUPLICATE_REFERENCE: {parent_id}]"

            output_records.append({
                "chunk_id": chunk_id,
                "fusion_score": round(combined_score, 4),
                "content": child_text,
                "parent_id": parent_id,
                "parent_text": parent_text,
                "concepts": [c for c in record.get("concepts", []) if c] if record else []
            })
        return output_records

    async def _hybrid_search_logic(self, http_client: httpx.AsyncClient, query: str, top_k: int) -> dict:
        return {"sorted_chunks": [], "lineage_records": {}, "text_cache": {}}