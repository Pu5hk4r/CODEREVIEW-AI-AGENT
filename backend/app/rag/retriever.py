"""
app/rag/retriever.py — Retrieves relevant code chunks from pgvector.

PHASE 5 — Requires DATABASE_URL and indexed codebase.
Falls back gracefully if DB not available.
"""
import logging
from app.rag.embedder import embed_texts

logger = logging.getLogger(__name__)


def retrieve_context(diff: str, top_k: int = 3) -> str:
    """
    Retrieves the most similar code chunks to the PR diff.

    Returns a formatted string with context — passed to the LLM.
    Raises an exception if DB is not available (handled by analyze_node).
    """
    import asyncio
    return asyncio.run(_async_retrieve(diff, top_k))


async def _async_retrieve(diff: str, top_k: int) -> str:
    from app.db.database import get_session
    from app.db.models import CodeEmbedding
    from sqlalchemy import text

    # Embed the diff to find similar chunks
    query_text = f"Code diff:\n{diff[:2000]}"
    query_embedding = embed_texts([query_text])[0]

    embedding_str = "[" + ",".join(map(str, query_embedding.tolist())) + "]"

    async with get_session() as session:
        # pgvector cosine similarity search
        sql = text("""
            SELECT file_path, content, start_line, end_line,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM code_embeddings
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)
        result = await session.execute(
            sql,
            {"embedding": embedding_str, "top_k": top_k},
        )
        rows = result.fetchall()

    if not rows:
        return "No similar code found in the indexed codebase."

    context_parts = ["## Relevant Codebase Context\n"]
    for row in rows:
        context_parts.append(
            f"### {row.file_path} (lines {row.start_line}-{row.end_line}) "
            f"[similarity: {row.similarity:.2f}]\n"
            f"```\n{row.content[:800]}\n```\n"
        )

    return "\n".join(context_parts)
