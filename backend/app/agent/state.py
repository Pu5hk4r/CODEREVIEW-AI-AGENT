"""
app/agent/state.py — AgentState flows through every node in the LangGraph.

All fields are Optional so nodes can be tested independently.
"""
from typing import Optional, TypedDict
from app.models.review import ReviewResult


class AgentState(TypedDict, total=False):
    # Input (set before graph runs)
    repo_name:     str          # e.g. "octocat/Hello-World"
    pr_number:     int          # e.g. 42

    # Set by fetch_node
    pr_title:      str
    pr_author:     str
    diff:          str          # Full unified diff text
    changed_files: list[str]    # File paths that changed

    # Set by analyze_node
    rag_context:   str          # Similar code retrieved from pgvector
    file_summaries: dict        # {filename: short summary}

    # Set by review_node
    review_result: ReviewResult  # Structured Groq output

    # Set by post_node
    posted:        bool          # True if GitHub comments posted
    comment_urls:  list[str]     # URLs of posted GitHub comments

    # Error handling
    error:         Optional[str]
