# filepath: src/omega_mcp/tools/graph_search.py
from mcp.server.fastmcp import Context
from omega_mcp.logger import logger

async def execute_graph_search_tool(query: str, ctx: Context) -> str:
    """Pulls runtime client connections from lifecycle state and wraps results in structural XML."""

    logger.info(f"⚙️ [MCP Graph Search] Querying internal knowledge base for: '{query}'")
    # Matches the updated global server app state layout safely
    service = ctx.request_context.app_state.get("graph_rag_service") or getattr(ctx.engine, 'app_state', {}).get("graph_rag_service")
    
    if not service:
        return "<knowledge_source type='graph_vector' status='ERROR'><error>Engine Offline</error></knowledge_source>"

    records = await service.execute_search(query)
    if not records:
        return f"<knowledge_source type='graph_vector' query='{query}' status='EMPTY'/>"

    xml_blocks = [f"<knowledge_source type='graph_vector' query='{query}'>"]
    for rec in records:
        parent_segment = ""
        if rec['parent_id']:
            parent_segment = f"\n    <parent_lineage id='{rec['parent_id']}'>{rec['parent_text']}</parent_lineage>"
            
        xml_blocks.append(
            f"  <record id='{rec['chunk_id']}' score='{rec['fusion_score']}'>\n"
            f"    <specific_fact>{rec['content']}</specific_fact>{parent_segment}\n"
            f"    <semantic_entities>{', '.join(rec['concepts'])}</semantic_entities>\n"
            f"  </record>"
        )
    xml_blocks.append("</knowledge_source>")
    return "\n".join(xml_blocks)