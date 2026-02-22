"""
app/rag/embedder.py — Embeds code chunks and stores them in pgvector.

Uses sentence-transformers locally (free, no OpenAI needed).
Model: 'all-MiniLM-L6-v2' — fast, 384 dims, great for code.

PHASE 5 CHECKPOINT:
  python scripts/index_codebase.py --path ./your-repo
"""
import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

# Lazy load — sentence-transformers is large
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model (first time, ~30s)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("✅ Embedding model ready (384 dims)")
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Returns a numpy array of shape (len(texts), 384)."""
    model = get_embedding_model()
    return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)


async def index_chunks(chunks, db_session) -> int:
    """
    Embeds code chunks and upserts into pgvector table.

    Args:
        chunks: list of CodeChunk objects
        db_session: async SQLAlchemy session

    Returns:
        Number of chunks indexed.
    """
    from app.db.models import CodeEmbedding

    if not chunks:
        return 0

    texts = [f"File: {c.file_path}\n\n{c.content}" for c in chunks]
    embeddings = embed_texts(texts)

    count = 0
    for chunk, embedding in zip(chunks, embeddings):
        record = CodeEmbedding(
            chunk_id   = chunk.chunk_id,
            file_path  = chunk.file_path,
            content    = chunk.content,
            start_line = chunk.start_line,
            end_line   = chunk.end_line,
            embedding  = embedding.tolist(),
        )
        db_session.add(record)
        count += 1

    await db_session.commit()
    logger.info("✅ Indexed %d chunks into pgvector", count)
    return count
