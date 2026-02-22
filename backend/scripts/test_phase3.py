#!/usr/bin/env python3
"""
PHASE 3 TEST — Groq LLM direct test

Usage:
  # Set GROQ_API_KEY in .env first, then:
  python scripts/test_phase3.py

Tests Groq API directly — no GitHub, no agent, no DB needed.
Expected output: A structured code review printed to terminal.

Get free Groq key at: https://console.groq.com
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
settings = get_settings()

if not settings.groq_api_key:
    print("❌ GROQ_API_KEY not set in .env")
    print("   Get a free key at https://console.groq.com")
    sys.exit(1)

print(f"✅ Groq API key found: {settings.groq_api_key[:8]}...")
print(f"✅ Using model: {settings.groq_model}")
print()


MOCK_DIFF = """\
diff --git a/auth/views.py b/auth/views.py
--- a/auth/views.py
+++ b/auth/views.py
@@ -1,10 +1,20 @@
+import sqlite3
+
 from flask import request, jsonify
 
+SECRET_KEY = "hardcoded_secret_key_123"
+
 def login():
     username = request.form.get('username')
     password = request.form.get('password')
-    user = User.query.filter_by(username=username, password=password).first()
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    conn = sqlite3.connect('app.db')
+    user = conn.execute(query).fetchone()
     if user:
-        return jsonify({"token": user.generate_token()})
+        return jsonify({"token": SECRET_KEY + username})
     return jsonify({"error": "Invalid credentials"}), 401
"""


def test_groq_direct():
    print("🧠 Testing Groq API directly (no agent, no GitHub)...")
    print("─" * 50)

    from groq import Groq
    from app.agent.prompts import REVIEW_SYSTEM_PROMPT, REVIEW_USER_TEMPLATE

    client = Groq(api_key=settings.groq_api_key)

    user_prompt = REVIEW_USER_TEMPLATE.format(
        repo_name     = "test/repo",
        pr_number     = 1,
        pr_title      = "Add user authentication",
        pr_author     = "devuser",
        changed_files = "auth/views.py",
        rag_context   = "No context",
        diff          = MOCK_DIFF,
    )

    print(f"Sending to {settings.groq_model}...\n")

    response = client.chat.completions.create(
        model    = settings.groq_model,
        messages = [
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature = 0.1,
        max_tokens  = 2048,
    )

    import json
    raw = response.choices[0].message.content
    print("Raw response:")
    print(raw[:500], "..." if len(raw) > 500 else "")
    print()

    # Try to parse as JSON
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        data = json.loads(clean.strip())

        print("✅ Valid JSON response!")
        print(f"   Summary: {data.get('summary', '')[:100]}...")
        print(f"   Approved: {data.get('approved')}")
        print(f"   Issues found: {len(data.get('comments', []))}")
        for c in data.get("comments", []):
            icon = {"critical": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(c.get("severity"), "⚪")
            print(f"   {icon} [{c.get('severity', '').upper()}] {c.get('title')}")

        print(f"\n🎉 PHASE 3 CHECKPOINT PASSED!")
        print(f"   Groq is working and producing structured reviews!")
        print(f"   Tokens used: {response.usage.total_tokens}")

    except json.JSONDecodeError as e:
        print(f"⚠️  Response is not valid JSON: {e}")
        print("   This can happen — the agent handles this in production")


if __name__ == "__main__":
    test_groq_direct()
