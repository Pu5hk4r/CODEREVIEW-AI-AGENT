#!/usr/bin/env python3
"""
PHASE 1 TEST — Health check

Usage:
  # Terminal 1: start server
  uvicorn app.main:app --reload --port 8000

  # Terminal 2: run this
  python scripts/test_phase1.py

Expected output:
  ✅ /health OK: {"status": "ok", "version": "1.0.0", ...}
  ✅ /docs reachable
"""
import httpx
import sys
import json

BASE = "http://localhost:8000"


def test_health():
    print("🔍 Testing Phase 1: Health endpoint\n")

    try:
        r = httpx.get(f"{BASE}/health", timeout=5)
        r.raise_for_status()
        data = r.json()
        print(f"✅ GET /health → {r.status_code}")
        print(json.dumps(data, indent=2))
        assert data["status"] == "ok", "status should be 'ok'"
        print("\n🎉 PHASE 1 CHECKPOINT PASSED — Server is running!\n")
    except httpx.ConnectError:
        print("❌ Could not connect to localhost:8000")
        print("   Start the server first: uvicorn app.main:app --reload")
        sys.exit(1)


if __name__ == "__main__":
    test_health()
