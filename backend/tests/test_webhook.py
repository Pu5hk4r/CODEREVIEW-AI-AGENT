"""
tests/test_webhook.py — Unit tests for webhook endpoint.

Run: pytest tests/test_webhook.py -v
"""
import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_sig(payload: bytes, secret: str = "dev_secret") -> str:
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


PR_OPENED_PAYLOAD = {
    "action": "opened",
    "number": 1,
    "pull_request": {
        "number": 1,
        "title": "Test PR",
        "body": "Test",
        "state": "open",
        "html_url": "https://github.com/test/repo/pull/1",
        "user": {"login": "tester", "id": 1},
        "head": {"sha": "abc", "ref": "feature"},
        "base": {"sha": "def", "ref": "main"},
        "additions": 10,
        "deletions": 2,
        "changed_files": 1,
    },
    "repository": {
        "id": 1,
        "name": "repo",
        "full_name": "test/repo",
        "html_url": "https://github.com/test/repo",
        "private": False,
    },
    "sender": {"login": "tester", "id": 1},
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_webhook_ping():
    r = client.post(
        "/webhook",
        json={"zen": "hello"},
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": "sha256=dummy"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "pong"


def test_webhook_pr_opened():
    body = json.dumps(PR_OPENED_PAYLOAD).encode()
    r = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": make_sig(body),
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "queued"
    assert data["pr"] == 1


def test_webhook_ignored_action():
    payload = {**PR_OPENED_PAYLOAD, "action": "closed"}
    body = json.dumps(payload).encode()
    r = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": make_sig(body),
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
