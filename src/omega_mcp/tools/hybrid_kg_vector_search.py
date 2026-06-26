# filepath: src/omega_mcp/tools/hybrid_kg_vector_search.py
import logging
from neo4j import AsyncGraphDatabase
import chromadb
from omega_mcp.logger import logger
from omega_mcp.config import settings

# =========================================================
# 1. INFRASTRUCTURE LAYER (Your Database Connections)
# =========================================================
class GraphRagClient:
    """
    Infrastructure client for executing Relative Score Fusion (RSF) and Graph RAG.
    Consolidated alongside its tool definition utilizing master singleton configurations.
    """
    def __init__(self):
        # Bind variables cleanly from the centralized settings schema
        self.neo4j_uri = settings.db.NEO4J_URI
        self.neo4j_user = settings.db.NEO4J_USER
        self.neo4j_password = settings.db.NEO4J_PASSWORD
        
        self.chroma_host = settings.db.CHROMA_HOST
        self.chroma_port = settings.db.CHROMA_PORT
        
        # Instantiate active network service connections
        self.neo4j_driver = AsyncGraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        self.chroma_client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)

    async def hybrid_search(self, query: str, top_k: int = 3) -> dict:
        """Executes RSF + Cypher lineages. Returns a raw Python dictionary."""
        combined_scores = {}
        chunk_text_cache = {}

        # Path A: Chroma HttpClient Query
        try:
            collection = self.chroma_client.get_or_create_collection("system_docs")
            vector_res = collection.query(query_texts=[query], n_results=5)
            v_docs = vector_res.get("documents", [[]])[0] if vector_res else []
            v_ids = vector_res.get("ids", [[]])[0] if vector_res else []
            v_distances = vector_res.get("distances", [[]])[0] if vector_res else []
            
            vector_hits = [(str(cid), 1.0 / (1.0 + float(dist))) for cid, dist in zip(v_ids, v_distances)]
            for cid, doc in zip(v_ids, v_docs):
                chunk_text_cache[str(cid)] = str(doc)
                
            if vector_hits:
                max_v_score = max(hit[1] for hit in vector_hits)
                for cid, score in vector_hits:
                    combined_scores[cid] = combined_scores.get(cid, 0.0) + (score / max_v_score)
        except Exception as e:
            logger.error(f"Chroma network hit failed: {e}")

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
                    max_f_score = max(hit[1] for hit in keyword_hits)
                    for cid, score in keyword_hits:
                        combined_scores[cid] = combined_scores.get(cid, 0.0) + (score / max_f_score)
        except Exception as e:
            logger.error(f"Neo4j keyword hit failed: {e}")

        if not combined_scores:
            return {"sorted_chunks": [], "lineage_records": {}, "text_cache": {}}

        sorted_chunks = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        target_ids = [item[0] for item in sorted_chunks]

        # Path C: Extract Graph Connections
        graph_lineage_cypher = """
        MATCH (c:DocumentNode) WHERE c.id IN $chunk_ids
        OPTIONAL MATCH (c)-[:CHILD_OF]->(p:DocumentNode)
        OPTIONAL MATCH (entity)-[:MENTIONED_IN]->(c)
        RETURN c.id AS chunk_id, p.id AS parent_id, 
               coalesce(p.text, p.content, p.body, '') AS parent_text, 
               collect(DISTINCT coalesce(entity.id, entity.name, '')) AS concepts
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
        except Exception as e:
            logger.error(f"Graph links failed: {e}")
            return {"sorted_chunks": sorted_chunks, "lineage_records": {}, "text_cache": chunk_text_cache}

# Instantiate the local file singleton driver instance
_graph_rag_client = GraphRagClient()


# =========================================================
# 2. APPLICATION/PRESENTATION LAYER (Your Formatting Wrapper)
# =========================================================
async def execute_hybrid_rsf_graph_rag(query: str) -> str:
    """Consolidates raw DB values into clean strings for the Agent."""
    logger.info(f"Triggering full pipeline execution: '{query}'")
    raw_payload = await _graph_rag_client.hybrid_search(query)
    
    sorted_chunks = raw_payload.get("sorted_chunks", [])
    record_map = raw_payload.get("lineage_records", {})
    chunk_text_cache = raw_payload.get("text_cache", {})

    if not sorted_chunks:
        return f"No database context elements located matching: '{query}'"

    formatted_output = ["INTERNAL FACT ENTITIES (HYBRID GRAPH-VECTOR):"]
    seen_parent_ids = set()

    for chunk_id, combined_score in sorted_chunks:
        child_text = chunk_text_cache.get(chunk_id, "[Text context payload missing]")
        record = record_map.get(chunk_id)
        
        formatted_output.append(
            f"\n[Source Citation ID: {chunk_id} | Pipeline RSF Score: {combined_score:.2f}]\n"
            f"Specific matching fact: '{child_text}'"
        )
        
        if record:
            parent_id = str(record.get("parent_id") or "").strip()
            parent_text = str(record.get("parent_text") or "").strip()
            concepts = [c for c in record.get("concepts", []) if c]
            
            if parent_id:
                # Deduplication Guard Engine
                if parent_id not in seen_parent_ids:
                    seen_parent_ids.add(parent_id)
                    if parent_text:
                        formatted_output.append(f" └── Full Parent Context ({parent_id}): '{parent_text}'")
                else:
                    formatted_output.append(f" └── Full Parent Context ({parent_id}): [OMITTED DUP - SEE PREVIOUS ENTRIES]")
                    
            if concepts:
                formatted_output.append(f" └── Connected Metadata Entities: {', '.join(concepts)}")

    return "\n".join(formatted_output)