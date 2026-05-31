#!/usr/bin/env python3
"""
scripts/evaluate_agent.py — LangSmith Evaluation Suite for CodeReview Agent

This script:
1. Seeds a benchmark dataset in LangSmith ("codereview-agent-eval")
2. Defines custom evaluators for:
   - Approval consistency
   - Critical issue recall
   - Warning detection
3. Runs the evaluation target using the agent's analyze & review nodes.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from app.config import get_settings
from langsmith import Client
from langsmith.evaluation import evaluate

# ── Mock PR Data for Benchmark ────────────────────────────────────────────────

VULNERABLE_DIFF = """\
diff --git a/auth/views.py b/auth/views.py
index 1234567..abcdefg 100644
--- a/auth/views.py
+++ b/auth/views.py
@@ -1,10 +1,22 @@
+import sqlite3
+
 from flask import request, jsonify
 
+JWT_SECRET = "super-secret-key-12345"
+
 def login():
     username = request.form.get('username')
     password = request.form.get('password')
-    user = User.query.filter_by(username=username, password=password).first()
+    # Direct query format allows SQL Injection
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    conn = sqlite3.connect('app.db')
+    user = conn.execute(query).fetchone()
     if user:
-        return jsonify({"token": user.generate_token()})
+        return jsonify({"token": JWT_SECRET + username})
     return jsonify({"error": "Invalid credentials"}), 401
"""

SECURE_DIFF = """\
diff --git a/auth/views.py b/auth/views.py
index abcdefg..9876543 100644
--- a/auth/views.py
+++ b/auth/views.py
@@ -1,22 +1,24 @@
 import sqlite3
+import os
 
 from flask import request, jsonify
 
-JWT_SECRET = "super-secret-key-12345"
+JWT_SECRET = os.environ.get("JWT_SECRET")
 
 def login():
     username = request.form.get('username')
     password = request.form.get('password')
-    # Direct query format allows SQL Injection
-    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
-    conn = sqlite3.connect('app.db')
-    user = conn.execute(query).fetchone()
-    if user:
-        return jsonify({"token": JWT_SECRET + username})
-    return jsonify({"error": "Invalid credentials"}), 401
+    if not JWT_SECRET:
+        return jsonify({"error": "Configuration error"}), 500
+
+    # Parameterized query protects against SQL injection
+    conn = sqlite3.connect('app.db')
+    cursor = conn.cursor()
+    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
+    user = cursor.fetchone()
+    if user:
+        return jsonify({"token": generate_secure_token(user, JWT_SECRET)})
+    return jsonify({"error": "Invalid credentials"}), 401
"""

EVAL_DATASET_NAME = "codereview-agent-eval"

BENCHMARK_CASES = [
    {
        "inputs": {
            "repo_name": "test/vulnerable-app",
            "pr_number": 101,
            "pr_title": "Implement simple user auth database lookup",
            "pr_author": "naive-coder",
            "changed_files": ["auth/views.py"],
            "diff": VULNERABLE_DIFF,
        },
        "outputs": {
            "approved": False,
            "expected_critical_vulnerabilities": ["sql injection", "sqli"],
            "expected_warnings": ["secret", "jwt_secret", "hardcoded"],
        }
    },
    {
        "inputs": {
            "repo_name": "test/secure-app",
            "pr_number": 102,
            "pr_title": "Use parameterized queries and secure env configuration",
            "pr_author": "security-champion",
            "changed_files": ["auth/views.py"],
            "diff": SECURE_DIFF,
        },
        "outputs": {
            "approved": True,
            "expected_critical_vulnerabilities": [],
            "expected_warnings": [],
        }
    }
]

# ── Target Function ───────────────────────────────────────────────────────────

def run_agent_evaluation_target(inputs: dict) -> dict:
    """
    Evaluation target wrapping the agent's analyze and review nodes.
    """
    from app.agent.nodes import analyze_node, review_node

    async def _run():
        state = {
            "repo_name": inputs.get("repo_name", "test/repo"),
            "pr_number": inputs.get("pr_number", 1),
            "pr_title": inputs.get("pr_title", "Eval PR"),
            "pr_author": inputs.get("pr_author", "eval-user"),
            "changed_files": inputs.get("changed_files", []),
            "diff": inputs.get("diff", ""),
        }
        
        # Execute the core agent review loop
        state = analyze_node(state)
        state = review_node(state)
        
        result = state.get("review_result")
        return {
            "approved": result.approved if result else False,
            "summary": result.summary if result else "",
            "comments": [c.model_dump() for c in result.comments] if result else []
        }

    try:
        return asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run())

# ── Custom Evaluators ─────────────────────────────────────────────────────────

def eval_approval(run, example) -> dict:
    """Evaluate if the approval status matches the reference."""
    ref = example.outputs or {}
    out = run.outputs or {}
    ref_approved = ref.get("approved")
    out_approved = out.get("approved")
    
    score = 1.0 if ref_approved == out_approved else 0.0
    return {"key": "approval_accuracy", "score": score}

def eval_critical_issues(run, example) -> dict:
    """Evaluate if expected critical vulnerabilities are detected."""
    ref = example.outputs or {}
    out = run.outputs or {}
    expected_vulns = ref.get("expected_critical_vulnerabilities", [])
    comments = out.get("comments", [])
    
    critical_comments = [c for c in comments if c.get("severity") == "critical"]
    
    if not expected_vulns:
        score = 1.0 if len(critical_comments) == 0 else 0.0
        return {"key": "critical_issue_recall", "score": score}
        
    found_count = 0
    for vuln in expected_vulns:
        vuln_lower = vuln.lower()
        for comment in critical_comments:
            text = f"{comment.get('title', '')} {comment.get('body', '')}".lower()
            if vuln_lower in text:
                found_count += 1
                break
                
    score = round(found_count / len(expected_vulns), 4)
    return {"key": "critical_issue_recall", "score": score}

def eval_warnings(run, example) -> dict:
    """Evaluate if warnings in expected_warnings are detected."""
    ref = example.outputs or {}
    out = run.outputs or {}
    expected_warnings = ref.get("expected_warnings", [])
    comments = out.get("comments", [])
    
    warning_comments = [c for c in comments if c.get("severity") in ("warning", "critical")]
    
    if not expected_warnings:
        score = 1.0 if len(warning_comments) == 0 else 0.0
        return {"key": "warning_issue_recall", "score": score}
        
    found_count = 0
    for warn in expected_warnings:
        warn_lower = warn.lower()
        for comment in warning_comments:
            text = f"{comment.get('title', '')} {comment.get('body', '')}".lower()
            if warn_lower in text:
                found_count += 1
                break
                
    score = round(found_count / len(expected_warnings), 4)
    return {"key": "warning_issue_recall", "score": score}

# ── Main Seeding & Evaluation Runner ──────────────────────────────────────────

def setup_and_run():
    settings = get_settings()
    
    if not settings.langsmith_api_key or settings.langsmith_api_key == "ls__your_key_here":
        print("[!] Error: LANGSMITH_API_KEY is not configured or is a placeholder in backend/.env.")
        print("    Please provide a valid LangSmith API key to enable evaluation.")
        sys.exit(1)

    print("[~] Connecting to LangSmith...")
    client = Client()

    # 1. Dataset Seeding
    try:
        dataset_exists = client.has_dataset(dataset_name=EVAL_DATASET_NAME)
        is_empty = True
        dataset_id = None
        
        if dataset_exists:
            ds = client.read_dataset(dataset_name=EVAL_DATASET_NAME)
            dataset_id = ds.id
            existing_examples = list(client.list_examples(dataset_id=dataset_id))
            is_empty = len(existing_examples) == 0
            
        if not dataset_exists:
            print(f"[*] Creating dataset '{EVAL_DATASET_NAME}'...")
            dataset = client.create_dataset(
                dataset_name=EVAL_DATASET_NAME,
                description="Evaluation suite for CodeReview Agent security/standards checks"
            )
            dataset_id = dataset.id
        elif is_empty:
            print(f"[*] Dataset '{EVAL_DATASET_NAME}' exists but is empty. Seeding examples...")
        else:
            print(f"[+] Dataset '{EVAL_DATASET_NAME}' already exists with {len(existing_examples)} examples.")
            
        if not dataset_exists or is_empty:
            import inspect
            sig = inspect.signature(client.create_examples)
            if "examples" in sig.parameters:
                client.create_examples(
                    dataset_id=dataset_id,
                    examples=BENCHMARK_CASES
                )
            else:
                inputs = [case["inputs"] for case in BENCHMARK_CASES]
                outputs = [case["outputs"] for case in BENCHMARK_CASES]
                client.create_examples(
                    dataset_id=dataset_id,
                    inputs=inputs,
                    outputs=outputs
                )
            print(f"[+] Seeded {len(BENCHMARK_CASES)} evaluation cases.")
    except Exception as e:
        print(f"[-] Failed to setup dataset in LangSmith: {e}")
        sys.exit(1)

    # 2. Run Evaluation
    print(f"[*] Running LangSmith evaluation on '{EVAL_DATASET_NAME}'...")
    try:
        results = evaluate(
            run_agent_evaluation_target,
            data=EVAL_DATASET_NAME,
            evaluators=[eval_approval, eval_critical_issues, eval_warnings],
            experiment_prefix="codereview-agent-base"
        )
        print("\n[+] Evaluation complete!")
        if hasattr(results, "url"):
            print(f"--> View results on LangSmith: {results.url}")
        else:
            print(f"--> View results on your LangSmith dashboard under the '{EVAL_DATASET_NAME}' dataset.")
    except Exception as e:
        import traceback
        print(f"[-] Evaluation run failed:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_and_run()
