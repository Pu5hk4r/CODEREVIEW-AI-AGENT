"""
app/github/pr_fetcher.py — Fetches PR diff, files, and metadata.

PHASE 2/6 — Requires GITHUB_TOKEN env var.
"""
import logging
import ssl
import urllib3
from github import Github, GithubException
from github import GithubRetry
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_gh_client = None

def get_github_client() -> Github:
    global _gh_client
    if _gh_client is None:
        retry = GithubRetry(
            total=10,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],
        )
        _gh_client = Github(
            settings.github_token,
            retry=retry,
            timeout=30,
        )
    return _gh_client


def fetch_pr_data(repo_name: str, pr_number: int) -> dict:
    """
    Fetches everything needed for a code review.

    Returns:
        {
          "pr_title": str,
          "pr_author": str,
          "diff": str,           # Full unified diff
          "changed_files": list  # File paths
        }
    """
    gh = get_github_client()

    try:
        repo = gh.get_repo(repo_name)
        pr   = repo.get_pull(pr_number)

        # Get list of changed files
        files = list(pr.get_files())
        changed_files = [f.filename for f in files]

        # Build unified diff string from file patches
        diff_parts = []
        for f in files:
            if f.patch:  # Binary files have no patch
                diff_parts.append(
                    f"diff --git a/{f.filename} b/{f.filename}\n"
                    f"--- a/{f.filename}\n"
                    f"+++ b/{f.filename}\n"
                    f"{f.patch}"
                )

        diff = "\n".join(diff_parts)

        logger.info(
            "✅ Fetched PR #%s: '%s' by %s | %d files | %d diff chars",
            pr_number, pr.title, pr.user.login, len(files), len(diff),
        )

        return {
            "pr_title":     pr.title,
            "pr_author":    pr.user.login,
            "diff":         diff,
            "changed_files": changed_files,
        }

    except GithubException as e:
        logger.error("GitHub API error for PR #%s: %s %s", pr_number, e.status, e.data)
        raise