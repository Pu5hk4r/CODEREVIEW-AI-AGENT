"""
app/services/review_service.py — Orchestrates a complete PR review run.

Called from:
  - webhook.py (background task, triggered by GitHub)
  - scripts/test_agent.py (direct testing)
"""
import logging
from app.agent.graph import get_review_graph

logger = logging.getLogger(__name__)


class ReviewService:
    @staticmethod
    async def run_review(repo_name: str, pr_number: int) -> dict:
        """
        Runs the full review pipeline for a single PR.

        Args:
            repo_name: GitHub repo full name, e.g. "octocat/Hello-World"
            pr_number: Pull request number

        Returns:
            Final AgentState dict after all nodes complete.
        """
        logger.info("🚀 Starting review: %s PR #%s", repo_name, pr_number)

        initial_state = {
            "repo_name": repo_name,
            "pr_number": pr_number,
        }

        graph = get_review_graph()

        try:
            final_state = await graph.ainvoke(initial_state)
            result = final_state.get("review_result")

            if result:
                logger.info(
                    "🎉 Review complete — PR #%s | approved=%s | "
                    "critical=%d warnings=%d suggestions=%d",
                    pr_number,
                    result.approved,
                    result.critical_count,
                    result.warning_count,
                    result.suggestion_count,
                )
            else:
                logger.warning("⚠️  Review completed but no result generated")

            return final_state

        except Exception as e:
            logger.error("💥 Review pipeline failed for PR #%s: %s", pr_number, e)
            raise
