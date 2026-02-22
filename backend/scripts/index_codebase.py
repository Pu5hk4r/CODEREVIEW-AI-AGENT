#!/usr/bin/env python3
"""
PHASE 5 SCRIPT — Index a codebase into pgvector for RAG

Usage:
  python scripts/index_codebase.py --path /path/to/your/repo

This embeds all Python/JS/TS files and stores them in pgvector.
After running this, the review agent will have codebase context.

Prerequisites:
  - DATABASE_URL set in .env pointing to running Postgres with pgvector
  - Run: docker-compose up db  (starts Postgres with pgvector)

PHASE 5 CHECKPOINT:
  Run this script → "Indexed N chunks" message
  Then run test_phase4.py again → rag_context will be non-empty
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()


SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".rs"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}


def collect_files(root_path: Path) -> list[Path]:
    files = []
    for path in root_path.rglob("*"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix in SUPPORTED_EXTENSIONS and path.is_file():
            if path.stat().st_size < 100_000:  # Skip files > 100KB
                files.append(path)
    return files


async def index_repo(repo_path: str):
    from app.rag.chunker import chunk_file
    from app.rag.embedder import index_chunks
    from app.db.database import init_db, get_session

    root = Path(repo_path).resolve()
    if not root.exists():
        print(f"❌ Path not found: {root}")
        sys.exit(1)

    print(f"📂 Indexing: {root}")
    await init_db()
    print("✅ Database ready")

    files = collect_files(root)
    print(f"📄 Found {len(files)} code files to index\n")

    total_chunks = 0
    for i, file_path in enumerate(files):
        rel_path = str(file_path.relative_to(root))
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            chunks = chunk_file(rel_path, content)

            async with get_session() as session:
                count = await index_chunks(chunks, session)
                total_chunks += count

            print(f"  [{i+1}/{len(files)}] {rel_path} → {count} chunks")
        except Exception as e:
            print(f"  ⚠️  Skipped {rel_path}: {e}")

    print(f"\n🎉 PHASE 5 CHECKPOINT: Indexed {total_chunks} chunks from {len(files)} files!")
    print("   RAG context is now available in code reviews.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index a codebase for RAG")
    parser.add_argument("--path", default=".", help="Path to the repo to index")
    args = parser.parse_args()
    asyncio.run(index_repo(args.path))
