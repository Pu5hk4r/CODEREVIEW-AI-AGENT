"""
app/github/comment_poster.py — Posts review comments to a GitHub PR.

PHASE 6 — Requires GITHUB_TOKEN with repo scope.
"""
import logging
from github import Github, GithubException
from app.config import get_settings
from app.models.review import ReviewResult, Severity

settings = get_settings()
logger = logging.getLogger(__name__)


SEVERITY_EMOJI = {
    Severity.CRITICAL:   "🔴",
    Severity.WARNING:    "🟡",
    Severity.SUGGESTION: "🔵",
}


def post_review_comments(
    repo_name: str,
    pr_number: int,
    result: ReviewResult,
) -> list[str]:
    """
    Posts a PR review with inline comments to GitHub.

    Returns list of comment HTML URLs.
    """
    gh   = Github(settings.github_token)
    repo = gh.get_repo(repo_name)
    pr   = repo.get_pull(pr_number)

    # ── Build summary body ────────────────────────────────────────────────────
    verdict = "✅ **APPROVED** — Safe to merge" if result.approved else "❌ **CHANGES REQUESTED**"
    summary_body = f"""## 🤖 AI Code Review

{verdict}

{result.summary}

---
**Issues Found:** 🔴 {result.critical_count} Critical · 🟡 {result.warning_count} Warnings · 🔵 {result.suggestion_count} Suggestions

*Reviewed by [CodeReview AI Agent](https://github.com) powered by Groq Llama 3.1 70B*
"""

    comment_urls = []

    # ── Post summary as PR comment ────────────────────────────────────────────
    try:
        summary_comment = pr.create_issue_comment(summary_body)
        comment_urls.append(summary_comment.html_url)
        logger.info("✅ Posted summary comment")
    except GithubException as e:
        logger.error("Failed to post summary: %s", e)

    # ── Post individual inline comments ───────────────────────────────────────
    # Note: inline comments require the diff position — we post as issue comments
    # for reliability. True inline requires commit SHA + diff position mapping.
    for comment in result.comments:
        emoji   = SEVERITY_EMOJI.get(comment.severity, "⚪")
        location = f"`{comment.file_path}`"
        if comment.line_number:
            location += f" line {comment.line_number}"

        body = f"""{emoji} **[{comment.severity.upper()}]** {comment.title}

**Location:** {location}

{comment.body}
"""
        if comment.suggestion:
            body += f"\n**Suggested fix:**\n```\n{comment.suggestion}\n```"

        try:
            c = pr.create_issue_comment(body)
            comment_urls.append(c.html_url)
        except GithubException as e:
            logger.error("Failed to post comment '%s': %s", comment.title, e)

    return comment_urls
