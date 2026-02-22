"""
app/api/webhook.py — GitHub webhook endpoint.

PHASE 2 CHECKPOINT:
  1. Create a GitHub repo webhook pointing to https://<your-ngrok>.ngrok.io/webhook
  2. Open a PR → check your terminal logs
  3. You should see: "📥 PR #X opened in owner/repo"

  Test with curl (simulated):
  curl -X POST http://localhost:8000/webhook \
    -H "Content-Type: application/json" \
    -H "X-GitHub-Event: pull_request" \
    -H "X-Hub-Signature-256: sha256=<hmac>" \
    -d @tests/fixtures/pr_opened.json
"""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.config import get_settings
from app.services.review_service import ReviewService

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify HMAC-SHA256 signature from GitHub."""
    if not settings.github_webhook_secret:
        logger.warning("⚠️  No webhook secret set — skipping signature verification")
        return True  # Dev mode

    if not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@router.post("")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    """
    Receives GitHub webhook events.
    Returns 200 immediately — review runs async in background.
    """
    raw_body = await request.body()

    # ── Signature verification ──────────────────────────────────────────────
    if not verify_signature(raw_body, x_hub_signature_256):
        logger.warning("❌ Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # ── Parse payload ────────────────────────────────────────────────────────
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # ── Handle pull_request events ───────────────────────────────────────────
    if x_github_event == "pull_request":
        action     = data.get("action", "")
        pr_number  = data.get("pull_request", {}).get("number")
        repo_name  = data.get("repository", {}).get("full_name", "unknown/repo")
        pr_title   = data.get("pull_request", {}).get("title", "")

        if action in ("opened", "synchronize"):
            logger.info("📥 PR #%s %s in %s — '%s'", pr_number, action, repo_name, pr_title)

            # Non-blocking: return 200 to GitHub immediately
            background_tasks.add_task(
                ReviewService.run_review,
                repo_name=repo_name,
                pr_number=pr_number,
            )

            return {"status": "queued", "pr": pr_number, "repo": repo_name}

        logger.info("⏭️  Ignoring PR action '%s'", action)

    elif x_github_event == "ping":
        logger.info("🏓 Ping received from GitHub — webhook configured correctly!")
        return {"status": "pong"}

    else:
        logger.info("⏭️  Ignoring event type '%s'", x_github_event)

    return {"status": "ignored"}
