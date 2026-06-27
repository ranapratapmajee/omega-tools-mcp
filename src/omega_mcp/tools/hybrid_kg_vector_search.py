# filepath: src/omega_mcp/tools/hybrid_kg_vector_search.py
import logging
import requests
from neo4j import AsyncGraphDatabase
import chromadb
from omega_mcp.logger import logger
from omega_mcp.config import settings

# Configure upstream logging frameworks to stay quiet
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

# =========================================================
# 1. INFRASTRUCTURE LAYER (Adaptive DB Connections)
# =========================================================
class GraphRagClient:
    """
    Infrastructure client for executing Relative Score Fusion (RSF) and Graph RAG.
    Consolidated alongside its tool definition utilizing master singleton configurations.
    """
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
        self.chroma_client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)

    def _generate_embedding(self, text_content: str) -> list:
        try:
            resp = requests.post(
                self.embedding_url, 
                json={"model": self.model_name, "prompt": text_content}, 
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("embedding", [])
        except Exception:
            return []

    async def hybrid_search(self, query: str, top_k: int = 3) -> dict:
        """Executes RSF + Adaptive Cypher lineages with suppressed telemetry logging."""
        combined_scores = {}
        chunk_text_cache = {}

        # Path A: Chroma HttpClient Query
        try:
            collection = self.chroma_client.get_or_create_collection(self.chroma_collection)
            query_vector = self._generate_embedding(query)
            
            if query_vector:
                vector_res = collection.query(query_embeddings=[query_vector], n_results=5)
                v_docs = vector_res.get("documents", [[]])[0] if vector_res else []
                v_ids = vector_res.get("ids", [[]])[0] if vector_res else []
                v_distances = vector_res.get("distances", [[]])[0] if vector_res else []
                
                vector_hits = []
                for cid, dist in zip(v_ids, v_distances):
                    d_val = float(dist)
                    score = 1.0 / (1.0 + d_val) if d_val >= 0 else abs(d_val)
                    vector_hits.append((str(cid), score))
                    
                for cid, doc in zip(v_ids, v_docs):
                    chunk_text_cache[str(cid)] = str(doc)
                    
                if vector_hits:
                    max_v_score = max(hit[1] for hit in vector_hits) or 1.0
                    for cid, score in vector_hits:
                        combined_scores[cid] = combined_scores.get(cid, 0.0) + (score / max_v_score)
        except Exception:
            pass

        # Path B: Neo4j Lucene Index Query
        keyword_cypher = """
        CALL db.index.fulltext.queryNodes("document_keyword_index", $search_phrase) 
        YIELD node, score RETURN node.id AS chunk_id, node.text AS text, score LIMIT 5
        """
        try:
            async with self.neo4j_driver.session() as session:
                res = await session.run(keyword_cypher, search_phrase=query)
                records = await res.data()
                keyword_hits = [(str(rec["chunk_id"]), float(rec["score"])) for rec in records]
                for rec in records:
                    cid = str(rec["chunk_id"])
                    if cid not in chunk_text_cache and rec["text"]:
                        chunk_text_cache[cid] = str(rec["text"])
                        
                if keyword_hits:
                    max_f_score = max(hit[1] for hit in keyword_hits) or 1.0
                    for cid, score in keyword_hits:
                        combined_scores[cid] = combined_scores.get(cid, 0.0) + (score / max_f_score)
        except Exception:
            pass

        if not combined_scores:
            return {"sorted_chunks": [], "lineage_records": {}, "text_cache": {}}

        sorted_chunks = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        target_ids = [item[0] for item in sorted_chunks]

        # Path C: Dynamic/Adaptive Extract Graph Connections
        graph_lineage_cypher = """
        MATCH (c:DocumentNode) WHERE c.id IN $chunk_ids
        OPTIONAL MATCH (c)-[:CHILD_OF]->(p:DocumentNode)
        OPTIONAL MATCH (entity)-[:MENTIONED_IN]->(c)
        
        WITH c, p, entity, properties(p) AS raw_props
        WITH c, p, entity, raw_props,
             [k IN keys(raw_props) WHERE NOT k IN ['id', 'type', 'created_at'] | raw_props[k]] AS dynamic_values
        
        RETURN c.id AS chunk_id, 
               p.id AS parent_id, 
               coalesce(raw_props.text, raw_props.content, raw_props.body, dynamic_values[0], '') AS parent_text, 
               collect(DISTINCT coalesce(entity.id, '')) AS concepts
        """
        try:
            async with self.neo4j_driver.session() as session:
                res = await session.run(graph_lineage_cypher, chunk_ids=target_ids)
                records = await res.data()
                return {
                    "sorted_chunks": sorted_chunks,
                    "lineage_records": {str(r["chunk_id"]): r for r in records},
                    "text_cache": chunk_text_cache
                }
        except Exception:
            return {"sorted_chunks": sorted_chunks, "lineage_records": {}, "text_cache": chunk_text_cache}

_graph_rag_client = GraphRagClient()


# =========================================================
# 2. APPLICATION/PRESENTATION LAYER (Standardized XML)
# =========================================================
async def execute_hybrid_rsf_graph_rag(query: str) -> str:
    """Consolidates raw DB values into clean XML text payloads for symmetrical LLM synthesis."""
    logger.info(f"🛰️ [MCP GRAPHRAG] Querying vector-graph indexes for: '{query}'")
    
    raw_payload = await _graph_rag_client.hybrid_search(query)
    sorted_chunks = raw_payload.get("sorted_chunks", [])
    record_map = raw_payload.get("lineage_records", {})
    chunk_text_cache = raw_payload.get("text_cache", {})

    if not sorted_chunks:
        return f"<knowledge_source type='graph_vector' status='EMPTY' query='{query}'/>"

    # Standardized markup schema exactly aligning with web search blocks
    formatted_output = [f"## INTERNAL KNOWLEDGE RETRIEVAL PACKET\n<knowledge_source type='graph_vector' query='{query}'>"]
    seen_parent_ids = set()

    for chunk_id, combined_score in sorted_chunks:
        child_text = chunk_text_cache.get(chunk_id, "").strip()
        record = record_map.get(chunk_id)
        
        parent_id = "N/A"
        parent_text = "N/A"
        concepts_str = "[]"
        
        if record:
            parent_id = str(record.get("parent_id") or "N/A").strip()
            concepts = [c for c in record.get("concepts", []) if c]
            if concepts:
                concepts_str = f"[{', '.join(concepts)}]"
            
            if parent_id and parent_id != "N/A":
                if parent_id not in seen_parent_ids:
                    seen_parent_ids.add(parent_id)
                    parent_text = str(record.get("parent_text") or "N/A").strip()
                else:
                    parent_text = f"[OMITTED_DUPLICATE_REFERENCE: SEE PREVIOUS BLOCKS FOR {parent_id}]"

        # Structural match ensures the agent's attention loops do not prioritize one tool over another
        item_payload = (
            f"  <record id='{chunk_id}' type='graph_vector'>\n"
            f"    <specific_fact>{child_text}</specific_fact>\n"
            f"    <parent_lineage id='{parent_id}'>{parent_text}</parent_lineage>\n"
            f"    <semantic_entities>{concepts_str}</semantic_entities>\n"
            f"  </record>"
        )
        formatted_output.append(item_payload)

    formatted_output.append("</knowledge_source>")
    return "\n".join(formatted_output)