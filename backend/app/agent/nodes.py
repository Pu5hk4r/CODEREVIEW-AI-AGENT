"""
app/agent/nodes.py — The four nodes of the review graph.

Flow: fetch_node → analyze_node → review_node → post_node

Each node receives AgentState, mutates it, returns updated state.
"""
import json
import logging
from typing import Any

from app.agent.state import AgentState
from app.agent.prompts import (
    ANALYZE_SYSTEM_PROMPT, ANALYZE_USER_TEMPLATE,
    REVIEW_SYSTEM_PROMPT, REVIEW_USER_TEMPLATE,
)
from app.config import get_settings
from app.models.review import ReviewResult, ReviewComment, Severity

settings = get_settings()
logger = logging.getLogger(__name__)


# ── Groq client (lazy init) ───────────────────────────────────────────────────
_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def groq_chat(system: str, user: str, temperature: float = 0.1) -> str:
    """Single Groq chat completion — returns raw text."""
    client = get_groq_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content


# ── NODE 1: fetch_node ────────────────────────────────────────────────────────
def fetch_node(state: AgentState) -> AgentState:
    """
    Fetches PR diff, title, author, and changed files from GitHub.

    Phase 2-3: Uses real GitHub API via PyGithub.
    Phase 1 fallback: Uses mock data if no GITHUB_TOKEN set.
    """
    repo_name  = state["repo_name"]
    pr_number  = state["pr_number"]

    logger.info("📥 [fetch] Fetching PR #%s from %s", pr_number, repo_name)

    if not settings.github_token:
        # Phase 1/3 fallback — mock data for local testing
        logger.warning("⚠️  No GITHUB_TOKEN — using mock PR data")
        state.update({
            "pr_title":     "Add user authentication",
            "pr_author":    "devuser",
            "diff":         _mock_diff(),
            "changed_files": ["auth/views.py", "auth/models.py", "tests/test_auth.py"],
        })
        return state

    try:
        from app.github.pr_fetcher import fetch_pr_data
        pr_data = fetch_pr_data(repo_name, pr_number)
        state.update(pr_data)
        logger.info("✅ [fetch] Got diff: %d chars, %d files",
                    len(state.get("diff", "")), len(state.get("changed_files", [])))
    except Exception as e:
        logger.error("❌ [fetch] Failed: %s", e)
        state["error"] = f"fetch_node failed: {e}"

    return state


# ── NODE 2: analyze_node ──────────────────────────────────────────────────────
def analyze_node(state: AgentState) -> AgentState:
    """
    Summarises what changed per file + retrieves RAG context.

    Phase 3: LLM summarisation only.
    Phase 5+: Also queries pgvector for similar code context.
    """
    diff = state.get("diff", "")
    if not diff:
        state["rag_context"] = "No diff available."
        return state

    logger.info("🔍 [analyze] Summarising %d char diff", len(diff))

    # ── File summaries via Groq ───────────────────────────────────────────────
    try:
        raw = groq_chat(
            system=ANALYZE_SYSTEM_PROMPT,
            user=ANALYZE_USER_TEMPLATE.format(diff=diff[:8000]),  # truncate
        )
        summaries = json.loads(raw)
        state["file_summaries"] = summaries
        logger.info("✅ [analyze] Summarised %d files", len(summaries))
    except Exception as e:
        logger.warning("⚠️  [analyze] Summarisation failed: %s", e)
        state["file_summaries"] = {}

    # ── RAG context retrieval (Phase 5+) ─────────────────────────────────────
    try:
        from app.rag.retriever import retrieve_context
        rag_ctx = retrieve_context(diff, top_k=3)
        state["rag_context"] = rag_ctx
        logger.info("✅ [analyze] RAG context retrieved (%d chars)", len(rag_ctx))
    except Exception as e:
        logger.info("ℹ️  [analyze] RAG not available (Phase 5+): %s", e)
        state["rag_context"] = "No codebase context available yet (RAG not initialised)."

    return state


# ── NODE 3: review_node ───────────────────────────────────────────────────────
def review_node(state: AgentState) -> AgentState:
    """
    Calls Groq with the full diff + context to generate structured review.

    PHASE 3 MAIN CHECKPOINT — this is where Groq does the heavy lifting.
    """
    diff          = state.get("diff", "")
    rag_context   = state.get("rag_context", "")
    changed_files = state.get("changed_files", [])

    logger.info("🧠 [review] Calling Groq %s ...", settings.groq_model)

    user_prompt = REVIEW_USER_TEMPLATE.format(
        repo_name     = state.get("repo_name", "unknown"),
        pr_number     = state.get("pr_number", 0),
        pr_title      = state.get("pr_title", "Untitled"),
        pr_author     = state.get("pr_author", "unknown"),
        changed_files = ", ".join(changed_files),
        rag_context   = rag_context or "None",
        diff          = diff[:12000],  # stay within context limit
    )

    try:
        raw_response = groq_chat(REVIEW_SYSTEM_PROMPT, user_prompt)
        logger.debug("Raw Groq response: %s", raw_response[:500])

        # Strip potential markdown code fences from JSON
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        data = json.loads(clean)

        # Build ReviewResult from parsed JSON
        comments = [
            ReviewComment(
                file_path   = c.get("file_path", "unknown"),
                line_number = c.get("line_number"),
                severity    = Severity(c.get("severity", "suggestion").lower()),
                title       = c.get("title", "Issue"),
                body        = c.get("body", ""),
                suggestion  = c.get("suggestion"),
            )
            for c in data.get("comments", [])
        ]

        result = ReviewResult(
            summary  = data.get("summary", "Review complete."),
            approved = data.get("approved", False),
            comments = comments,
        )

        state["review_result"] = result
        logger.info(
            "✅ [review] Done — %d critical, %d warnings, %d suggestions | approved=%s",
            result.critical_count, result.warning_count,
            result.suggestion_count, result.approved,
        )

    except json.JSONDecodeError as e:
        logger.error("❌ [review] JSON parse failed: %s\nRaw: %s", e, raw_response[:300])
        state["error"] = f"review_node JSON parse failed: {e}"
    except Exception as e:
        logger.error("❌ [review] Failed: %s", e)
        state["error"] = f"review_node failed: {e}"

    return state


# ── NODE 4: post_node ─────────────────────────────────────────────────────────
def post_node(state: AgentState) -> AgentState:
    """
    Posts the review result as GitHub PR comments.

    Phase 3-5: Just logs to terminal.
    Phase 6+: Actually posts to GitHub via PyGithub.
    """
    result = state.get("review_result")
    if not result:
        logger.warning("⚠️  [post] No review result to post")
        state["posted"] = False
        return state

    repo_name  = state.get("repo_name", "")
    pr_number  = state.get("pr_number", 0)

    logger.info("💬 [post] Posting review for PR #%s in %s", pr_number, repo_name)

    # Always log the review summary to terminal (visible from Phase 3 onwards)
    _log_review(result)

    # Phase 6+: post to GitHub
    if settings.github_token and repo_name and pr_number:
        try:
            from app.github.comment_poster import post_review_comments
            urls = post_review_comments(repo_name, pr_number, result)
            state["posted"]       = True
            state["comment_urls"] = urls
            logger.info("✅ [post] Posted %d comments to GitHub", len(urls))
        except Exception as e:
            logger.error("❌ [post] GitHub post failed: %s", e)
            state["posted"] = False
    else:
        logger.info("ℹ️  [post] GitHub posting skipped (no token or mock mode)")
        state["posted"]       = False
        state["comment_urls"] = []

    # Save to in-memory store (Phase 1-6) / DB (Phase 7+)
    _persist_review(state)

    return state


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_review(result: ReviewResult):
    """Pretty-print review to terminal."""
    print("\n" + "="*60)
    print("📋 CODE REVIEW RESULT")
    print("="*60)
    print(f"\n📝 Summary:\n{result.summary}")
    print(f"\n✅ Approved: {result.approved}")
    print(f"🔴 Critical: {result.critical_count}  🟡 Warnings: {result.warning_count}  🔵 Suggestions: {result.suggestion_count}")

    if result.comments:
        print("\n─── Issues ───────────────────────────────────────────────")
        for i, c in enumerate(result.comments, 1):
            icon = {"critical": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(c.severity, "⚪")
            print(f"\n{i}. {icon} [{c.severity.upper()}] {c.title}")
            print(f"   📄 {c.file_path}" + (f" line {c.line_number}" if c.line_number else ""))
            print(f"   {c.body}")
            if c.suggestion:
                print(f"   💡 Fix:\n{c.suggestion}")
    print("\n" + "="*60 + "\n")


def _persist_review(state: AgentState):
    """Save review to in-memory store (replaced by DB in Phase 7)."""
    import uuid
    from datetime import datetime, timezone
    from app.api.reviews import add_review_to_store

    result = state.get("review_result")
    if not result:
        return

    add_review_to_store({
        "id":             str(uuid.uuid4()),
        "repo_name":      state.get("repo_name"),
        "pr_number":      state.get("pr_number"),
        "pr_title":       state.get("pr_title"),
        "pr_author":      state.get("pr_author"),
        "reviewed_at":    datetime.now(timezone.utc).isoformat(),
        "approved":       result.approved,
        "critical_count": result.critical_count,
        "warning_count":  result.warning_count,
        "suggestion_count": result.suggestion_count,
        "summary":        result.summary,
        "comments":       [c.model_dump() for c in result.comments],
    })


def _mock_diff() -> str:
    """Mock diff for Phase 1/3 testing without a real GitHub token."""
    return """\
diff --git a/auth/views.py b/auth/views.py
index 1234567..abcdefg 100644
--- a/auth/views.py
+++ b/auth/views.py
@@ -1,15 +1,28 @@
+import sqlite3
+import os
+
 from flask import request, jsonify
 
+SECRET_KEY = "hardcoded_secret_key_123"  # TODO: move to env
+
 def login():
     username = request.form.get('username')
     password = request.form.get('password')
-    user = User.query.filter_by(username=username, password=password).first()
+    # Direct string interpolation — SQL injection vulnerability
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    conn = sqlite3.connect('app.db')
+    user = conn.execute(query).fetchone()
     if user:
-        return jsonify({"token": user.generate_token()})
+        return jsonify({"token": SECRET_KEY + username})  # Weak token
     return jsonify({"error": "Invalid credentials"}), 401
+
+def get_user_data(user_id):
+    # No authentication check
+    query = f"SELECT * FROM users WHERE id={user_id}"
+    conn = sqlite3.connect('app.db')
+    return conn.execute(query).fetchall()
"""
