"""
tests/test_agent.py — Unit tests for agent nodes and models.

Run: pytest tests/test_agent.py -v
"""
import pytest
from app.models.review import ReviewResult, ReviewComment, Severity
from app.rag.chunker import chunk_file, chunk_diff


def test_review_result_counts():
    """ReviewResult should auto-count severities."""
    result = ReviewResult(
        summary="Test review",
        approved=False,
        comments=[
            ReviewComment(file_path="a.py", severity=Severity.CRITICAL, title="SQL Injection", body="Fix it"),
            ReviewComment(file_path="b.py", severity=Severity.CRITICAL, title="Hardcoded key", body="Use env"),
            ReviewComment(file_path="c.py", severity=Severity.WARNING, title="Missing error handling", body="Add try/except"),
            ReviewComment(file_path="d.py", severity=Severity.SUGGESTION, title="Rename variable", body="Use descriptive name"),
        ],
    )
    assert result.critical_count   == 2
    assert result.warning_count    == 1
    assert result.suggestion_count == 1


def test_review_comment_optional_fields():
    """line_number and suggestion should be optional."""
    c = ReviewComment(
        file_path="app.py",
        severity=Severity.WARNING,
        title="Missing check",
        body="Add null check",
    )
    assert c.line_number is None
    assert c.suggestion is None


def test_chunk_file_basic():
    """chunk_file should split large files into chunks."""
    content = "\n".join([f"line {i}" for i in range(200)])
    chunks = chunk_file("test.py", content)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.file_path == "test.py"
        assert chunk.content.strip()
        assert chunk.chunk_id.startswith("test.py:")


def test_chunk_diff():
    """chunk_diff should extract changed files from unified diff."""
    diff = """\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,5 +1,8 @@
+import os
 from flask import request
+SECRET = "abc"
 def login():
     pass
diff --git a/models.py b/models.py
--- a/models.py
+++ b/models.py
@@ -10,3 +10,5 @@
 class User:
+    email = None
     pass
"""
    chunks = chunk_diff(diff)
    file_paths = [c.file_path for c in chunks]
    assert "auth.py" in file_paths
    assert "models.py" in file_paths


def test_severity_enum():
    assert Severity.CRITICAL   == "critical"
    assert Severity.WARNING    == "warning"
    assert Severity.SUGGESTION == "suggestion"
