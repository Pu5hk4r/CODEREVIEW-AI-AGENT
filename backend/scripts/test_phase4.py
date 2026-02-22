#!/usr/bin/env python3
"""
PHASE 4 TEST — Full LangGraph agent end-to-end

Usage:
  python scripts/test_phase4.py

Runs the complete 4-node agent pipeline:
  fetch → analyze → review → post

Uses mock GitHub data (no GITHUB_TOKEN needed).
Requires: GROQ_API_KEY

Expected output:
  ✅ fetch_node — mock PR data loaded
  ✅ analyze_node — files summarised
  ✅ review_node — Groq generated review
  ✅ post_node — review logged to terminal
  🎉 PHASE 4 CHECKPOINT PASSED
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


async def test_full_agent():
    print("🤖 Testing Phase 4: Full LangGraph Agent Pipeline")
    print("═" * 55)
    print()

    from app.config import get_settings
    settings = get_settings()

    if not settings.groq_api_key:
        print("❌ GROQ_API_KEY not set — see Phase 3 first")
        sys.exit(1)

    # Run the agent with a mock PR (no GitHub token needed)
    from app.agent.graph import build_review_graph

    print("Building review graph...")
    graph = build_review_graph()
    print("✅ Graph compiled\n")

    initial_state = {
        "repo_name": "test/demo-repo",
        "pr_number": 99,
    }

    print("Running graph: fetch → analyze → review → post\n")
    print("─" * 55)

    import time
    start = time.time()
    final_state = await graph.ainvoke(initial_state)
    elapsed = time.time() - start

    print("─" * 55)
    print()

    # Validate state
    errors = final_state.get("error")
    if errors:
        print(f"❌ Agent error: {errors}")
        sys.exit(1)

    result = final_state.get("review_result")
    if not result:
        print("❌ No review result generated")
        sys.exit(1)

    print(f"⏱️  Completed in {elapsed:.1f}s")
    print(f"✅ Summary: {result.summary[:120]}...")
    print(f"✅ Approved: {result.approved}")
    print(f"✅ Issues: 🔴 {result.critical_count} critical | 🟡 {result.warning_count} warnings | 🔵 {result.suggestion_count} suggestions")
    print()
    print("🎉 PHASE 4 CHECKPOINT PASSED!")
    print("   Full agent pipeline is working end-to-end.")
    print("   Next: Phase 5 (RAG) or Phase 6 (real GitHub posting)\n")


if __name__ == "__main__":
    asyncio.run(test_full_agent())
