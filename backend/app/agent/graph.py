"""
app/agent/graph.py — Builds the LangGraph review agent.

PHASE 4 CHECKPOINT:
  Run: python scripts/test_agent.py
  Should see all 4 nodes execute: fetch → analyze → review → post

The graph is compiled once and reused across requests.
"""
import logging
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import fetch_node, analyze_node, review_node, post_node

logger = logging.getLogger(__name__)


def should_continue(state: AgentState) -> str:
    """Conditional edge — abort graph if any node set an error."""
    if state.get("error"):
        logger.error("🛑 Graph aborting due to error: %s", state["error"])
        return "abort"
    return "continue"


def build_review_graph():
    """
    Builds and compiles the review agent state machine.

    Nodes:
      fetch   → Pull PR diff + metadata from GitHub
      analyze → Summarise files + retrieve RAG context
      review  → Call Groq to generate structured review
      post    → Post comments to GitHub PR

    Returns a compiled LangGraph runnable.
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("fetch",   fetch_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("review",  review_node)
    graph.add_node("post",    post_node)

    # Entry point
    graph.set_entry_point("fetch")

    # Edges with error checking
    graph.add_conditional_edges(
        "fetch",
        should_continue,
        {"continue": "analyze", "abort": END},
    )
    graph.add_conditional_edges(
        "analyze",
        should_continue,
        {"continue": "review", "abort": END},
    )
    graph.add_conditional_edges(
        "review",
        should_continue,
        {"continue": "post", "abort": END},
    )
    graph.add_edge("post", END)

    compiled = graph.compile()
    logger.info("✅ LangGraph review agent compiled (4 nodes)")
    return compiled


# Singleton graph — compiled once at module import
_review_graph = None

def get_review_graph():
    global _review_graph
    if _review_graph is None:
        _review_graph = build_review_graph()
    return _review_graph
