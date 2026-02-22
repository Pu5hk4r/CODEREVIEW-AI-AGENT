"""
app/rag/chunker.py — Splits code files into embeddable chunks.

PHASE 5 — Used when indexing a codebase for RAG context.
"""
import re
from dataclasses import dataclass


@dataclass
class CodeChunk:
    file_path:  str
    content:    str
    start_line: int
    end_line:   int
    chunk_id:   str  # "{file_path}:{start_line}-{end_line}"


def chunk_file(file_path: str, content: str, chunk_size: int = 50) -> list[CodeChunk]:
    """
    Splits a code file into overlapping chunks of ~chunk_size lines.
    Uses function/class boundaries when possible for semantic chunking.
    """
    lines = content.split("\n")
    chunks = []
    overlap = 10

    i = 0
    while i < len(lines):
        end = min(i + chunk_size, len(lines))

        # Try to find a natural break (blank line) near the end
        if end < len(lines):
            for j in range(end, max(i + overlap, end - 10), -1):
                if j < len(lines) and lines[j].strip() == "":
                    end = j
                    break

        chunk_lines = lines[i:end]
        chunk_content = "\n".join(chunk_lines)

        if chunk_content.strip():  # Skip empty chunks
            chunks.append(CodeChunk(
                file_path  = file_path,
                content    = chunk_content,
                start_line = i + 1,
                end_line   = end,
                chunk_id   = f"{file_path}:{i+1}-{end}",
            ))

        i = end - overlap  # Overlap for context continuity
        if i <= 0:
            i = end

    return chunks


def chunk_diff(diff: str) -> list[CodeChunk]:
    """
    Extracts changed code sections from a unified diff.
    Returns chunks of added/context lines grouped by file.
    """
    chunks = []
    current_file = None
    current_lines = []
    current_start = 1

    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            # Save previous file chunk
            if current_file and current_lines:
                chunks.append(CodeChunk(
                    file_path  = current_file,
                    content    = "\n".join(current_lines),
                    start_line = current_start,
                    end_line   = current_start + len(current_lines),
                    chunk_id   = f"{current_file}:diff",
                ))
            current_file  = line.split(" b/")[-1].strip()
            current_lines = []

        elif line.startswith("@@"):
            # Parse hunk header: @@ -l,s +l,s @@
            match = re.search(r"\+(\d+)", line)
            if match:
                current_start = int(match.group(1))

        elif current_file and not line.startswith("---") and not line.startswith("+++"):
            current_lines.append(line)

    # Don't forget the last file
    if current_file and current_lines:
        chunks.append(CodeChunk(
            file_path  = current_file,
            content    = "\n".join(current_lines),
            start_line = current_start,
            end_line   = current_start + len(current_lines),
            chunk_id   = f"{current_file}:diff",
        ))

    return chunks
