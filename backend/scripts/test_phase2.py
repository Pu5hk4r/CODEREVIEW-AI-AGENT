#!/usr/bin/env python3
"""
PHASE 2 TEST — GitHub webhook simulation

Usage:
  python scripts/test_phase2.py

Simulates a GitHub "pull_request opened" webhook event.
Watch your server terminal — you should see the PR logged.

Expected terminal output on server:
  📥 PR #42 opened in octocat/Hello-World — 'Add authentication feature'
"""
import hashlib
import hmac
import json
import httpx
import sys

BASE = "http://localhost:8000"

# Must match GITHUB_WEBHOOK_SECRET in your .env
# Set to empty string to skip signature check in dev
WEBHOOK_SECRET = "dev_secret"

MOCK_PAYLOAD = {
    "action": "opened",
    "number": 42,
    "pull_request": {
        "number": 42,
        "title": "Add authentication feature",
        "body": "This PR adds login/logout functionality",
        "state": "open",
        "html_url": "https://github.com/octocat/Hello-World/pull/42",
        "user": {"login": "devuser", "id": 1},
        "head": {"sha": "abc123", "ref": "feature/auth"},
        "base": {"sha": "def456", "ref": "main"},
        "additions": 150,
        "deletions": 10,
        "changed_files": 3,
    },
    "repository": {
        "id": 1296269,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "html_url": "https://github.com/octocat/Hello-World",
        "private": False,
    },
    "sender": {"login": "devuser", "id": 1},
}


def make_signature(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_webhook():
    print("🔍 Testing Phase 2: GitHub webhook receiver\n")

    body = json.dumps(MOCK_PAYLOAD).encode()
    signature = make_signature(body, WEBHOOK_SECRET)

    try:
        r = httpx.post(
            f"{BASE}/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
            },
            timeout=10,
        )
        print(f"Response: {r.status_code} — {r.text}")

        if r.status_code == 200:
            data = r.json()
            assert data.get("status") == "queued", f"Expected 'queued', got {data}"
            print("✅ Webhook received and queued")
            print("\n🎉 PHASE 2 CHECKPOINT PASSED!")
            print("   Check server terminal — PR should be logged there")
            print("   Review runs in background (will complete in a few seconds)\n")
        else:
            print(f"❌ Unexpected status: {r.status_code}")
            sys.exit(1)

    except httpx.ConnectError:
        print("❌ Server not running. Start with: uvicorn app.main:app --reload")
        sys.exit(1)


    # Also test ping
    r2 = httpx.post(
        f"{BASE}/webhook",
        json={"zen": "testing"},
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": "sha256=dummy"},
    )
    print(f"Ping response: {r2.json()}")


if __name__ == "__main__":
    test_webhook()
