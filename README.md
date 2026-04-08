# 🤖 CodeReview AI Agent

An AI agent that reviews Pull Requests like a senior engineer — powered by **Groq** (Llama 3.1 70B), **LangGraph**, **FastAPI**, and **pgvector RAG**.
![](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/GCP%20Production%20Review.png)

═══════════════════════════════════════════════════════════════════════════════════════
                              DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════════════════════

  1. Developer pushes bad code → opens PR on GitHub
  2. GitHub fires webhook → POST /webhook (HMAC signed)
  3. FastAPI verifies signature → returns 200 immediately
  4. Background task → starts LangGraph agent
  5. fetch_node → GitHub API → gets PR diff
  6. analyze_node → pgvector → retrieves similar code chunks
  7. review_node → Groq API → structured JSON review
  8. post_node → GitHub API → posts comments on PR
  9. post_node → PostgreSQL → saves review permanently
  10. Dashboard → GET /reviews → shows all past reviews


═══════════════════════════════════════════════════════════════════════════════════════
                           GCP DEPLOYMENT ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════════════

  GitHub ──▶ Cloud Run ──▶ Cloud SQL (Postgres + pgvector)
                │
                ├──▶ Secret Manager (API keys)
                │
                ├──▶ Container Registry (Docker image)
                │
                └──▶ Groq API (external)
                └──▶ GitHub API (external)


  Cloud Run:
    - Serverless — scales 0 to N automatically
    - Deployed from Docker container
    - Gets secrets from Secret Manager at runtime
    - Health check: GET /health

  Cloud SQL:
    - Managed PostgreSQL
    - pgvector extension enabled
    - Private network with Cloud Run
    - Automatic backups

  Secret Manager:
    - GROQ_API_KEY
    - GITHUB_TOKEN
    - GITHUB_WEBHOOK_SECRET
    - DATABASE_URL
    - Never in code or Dockerfile
---
# Dashboard
![Dashboard1](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/CodeReviewAgentDashboard.png)
![Dashboard2](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/CodeReviewAgentDashboard2.png)
---
# Generate CODE Review PR
![PR1](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/CodeReviewAgent_PR1.png)
![PR2](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/CodeReviewAgentPR2.png)

## 🚀 Phased Build Plan

| Phase | What I build | Checkpoint |
|-------|---------------|------------|
| **Phase 1** | Project setup + health endpoint | `GET /health` returns 200 |
| **Phase 2** | GitHub webhook receiver | Webhook logs PR events |
| **Phase 3** | Groq LLM integration | Code review from Groq in terminal |
| **Phase 4** | LangGraph agent (fetch → analyze → review → post) | Full agent run in terminal |
| **Phase 5** | pgvector RAG pipeline | Context-aware reviews |
| **Phase 6** | GitHub PR comments posting | Comments appear on real PRs |
| **Phase 7** | Database persistence | Reviews stored in PostgreSQL |
| **Phase 8** | React dashboard | Web UI showing past reviews |
| **Phase 9** | Docker + GCP Cloud Run deploy | Live production URL |

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| LLM | **Groq** (llama-3.1-70b-versatile) — free, blazing fast |
| Agent | LangGraph — stateful multi-step agent |
| API | FastAPI — async, webhook-native |
| RAG | pgvector + sentence-transformers |
| Queue | Background tasks (local) / GCP Cloud Tasks (prod) |
| GitHub | PyGithub |
| DB | PostgreSQL + SQLAlchemy async |
| Deploy | Docker + GCP Cloud Run |

---
## Testing - Testing Strategy — Phase by Phase (Before GCP Deployment)
Phase 1 → test_phase1.py  — server health
Phase 2 → test_phase2.py  — webhook signature
Phase 3 → manual          — Groq response
Phase 4 → manual          — agent pipeline
Phase 5 → check_db.py     — database tables
Phase 6 → real GitHub PR  — end to end
Phase 7 → check_db.py     — data persistence
Phase 8 → browser         — dashboard UI
---
## End-to-End Testing (full flow) 
Real PR opened on GitHub
         ↓
Webhook received
         ↓
Agent completed all 4 nodes
         ↓
Comment appeared on GitHub PR
         ↓
Review saved in PostgreSQL
         ↓
Dashboard showed review

---

## Manual Testing — Real PR Flow
Step 1: Created auth.py with known vulnerabilities
        - SQL injection (line 5)
        - Hardcoded secret (line 1)
        - No connection close

Step 2: Pushed to feature/bad-code-v2 branch

Step 3: Opened PR on GitHub

Step 4: Verified webhook received (ngrok logs)

Step 5: Verified agent ran all 4 nodes (server logs)

Step 6: Verified Groq found the SQL injection

Step 7: Verified comment appeared on GitHub PR

Step 8: Verified review saved in PostgreSQL

Step 9: Verified dashboard showed correct counts
---
## Performance Metrics
### Latency Metrics (measured during testing)
Operation                    Time        How Measured
────────────────────────────────────────────────────
Webhook receive + return 200  <100ms     ngrok logs
GitHub fetch PR diff          2-3s       server logs timestamp
RAG vector retrieval          <100ms     server logs timestamp
Groq LLM inference            2-5s       httpx logs
GitHub post comment           1-2s       server logs timestamp
PostgreSQL save               <500ms     server logs timestamp
────────────────────────────────────────────────────
TOTAL end to end              ~30-60s    wall clock time

### Throughput Metrics
Groq free tier limit:    30 requests/minute
Our usage:               1 review per PR
Concurrent reviews:      Limited by Groq rate limit
Max PRs per hour:        ~30 (Groq limit)

### Accuracy Metrics (manual evaluation)
Test PRs created: 3
Known issues planted: 4
Issues found by Groq: 3/4 (75%)

Issue 1: SQL Injection          → ✅ Found (CRITICAL)
Issue 2: Hardcoded Secret       → ✅ Found (CRITICAL)
Issue 3: No DB connection close → ✅ Found (SUGGESTION)
Issue 4: No input validation    → ❌ Missed

### Reliability Metrics
Webhooks received:  5
Webhooks processed: 5
Success rate:       100%

Reviews completed:  3
Reviews failed:     0
DB saves:           3/3
GitHub posts:       3/3

### 1. Functional Evaluation
✅ Does webhook receive events?        → Yes
✅ Does signature verify correctly?    → Yes
✅ Does agent complete all 4 nodes?    → Yes
✅ Does Groq find real issues?         → Yes (75%)
✅ Does comment appear on GitHub PR?   → Yes
✅ Does DB save persist?               → Yes
✅ Does dashboard show data?           → Yes

### 2. LLM Output Quality Evaluation
1. Correct severity classification
   CRITICAL for SQL injection ✅
   WARNING for missing functionality ✅
   SUGGESTION for minor improvements ✅

2. Accurate line numbers
   SQL injection at line 5 → Groq said line 5 ✅

3. Actionable fix suggestions
   Groq gave exact parameterized query fix ✅

4. No hallucinations
   Groq reviewed only what was in diff ✅
   Did not invent issues ✅
   
### 3. Prompt evaluation:
I tested 3 prompt versions:

V1: Simple — "review this code"
    Result: vague feedback, no structure

V2: Structured — "return JSON with severity"
    Result: correct structure, occasional uppercase

V3: Final — strict JSON schema + examples
    Result: consistent, parseable, accurate
    
### 4. Error Handling Evaluation
Scenario                          Result
──────────────────────────────────────────────
Empty PR diff                     ✅ Handled gracefully
Wrong webhook secret              ✅ Returns 401
Groq returns malformed JSON       ✅ Caught + logged
asyncio event loop conflict       ✅ Fixed with threading
Port conflict (5432)              ✅ Resolved with 5433
Uppercase severity from Groq      ✅ Fixed with .lower()

### 5. System Reliability Evaluation
What I monitored:
- Server logs (uvicorn + custom loggers)
- ngrok HTTP request logs
- PostgreSQL row counts
- GitHub PR comments

Log levels used:
INFO    → normal flow
WARNING → non-critical issues
ERROR   → failures needing attention


### 6. Automated Test Suite
#### pytest test suite
tests/
├── test_webhook.py      # signature verification
├── test_agent.py        # LangGraph nodes
├── test_groq.py         # LLM output parsing
├── test_github.py       # PR fetch + post
├── test_db.py           # CRUD operations
└── test_e2e.py          # full pipeline

## 7. Monitoring (GCP)
#### Request Latency per endpoint
  - Error rate
  - CPU/memory per Cloud Run instance

#### Cloud Logging:
  - Structured logs from FastAPI
  - Alert on ERROR level logs

#### Custom metrics:
  - Reviews per hour
  - Critical issues found per day
  - Average review time

  - 
### 8. LLM Evaluation Framework
#### Golden dataset:
  - 20 PRs with known issues
  - Expected: issue type, severity, line number

#### Metrics:
  - Precision: found issues that are real
  - Recall: found all issues that exist
  - F1 Score: balance of both
  - Hallucination rate: invented issues

#### Current manual result:
  Precision: 100% (no false positives)
  Recall:    75%  (missed 1 of 4 issues)
---

## ⚙️ Environment Variables

```env
# Required from Phase 1
GROQ_API_KEY=gsk_...               # Get free at console.groq.com

# Required from Phase 2
GITHUB_WEBHOOK_SECRET=your_secret
GITHUB_TOKEN=ghp_...               # Personal access token

# Required from Phase 5
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/codereview

# Optional (tracing)
LANGSMITH_API_KEY=ls__...
```

---

## 🏃 Quick Start

```bash
# Clone and setup
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env with your keys

# Phase 1 — Start server
uvicorn app.main:app --reload --port 8000
# Visit http://localhost:8000/health

# Phase 3 — Test Groq directly
python scripts/test_groq.py

# Phase 4 — Test full agent
python scripts/test_agent.py

# Run with Docker
docker-compose up --build
```

---

## 📁 Project Structure

```
codereview-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── webhook.py        # GitHub webhook endpoint
│   │   │   ├── reviews.py        # GET /reviews endpoints
│   │   │   └── health.py         # Health check
│   │   ├── agent/
│   │   │   ├── graph.py          # LangGraph state machine
│   │   │   ├── nodes.py          # fetch → analyze → review → post
│   │   │   ├── state.py          # AgentState TypedDict
│   │   │   └── prompts.py        # All prompts versioned here
│   │   ├── rag/
│   │   │   ├── embedder.py       # Embed code files
│   │   │   ├── retriever.py      # Query similar chunks
│   │   │   └── chunker.py        # Split code into chunks
│   │   ├── github/
│   │   │   ├── client.py         # PyGithub wrapper
│   │   │   ├── pr_fetcher.py     # Fetch PR diff + metadata
│   │   │   └── comment_poster.py # Post comments to PR
│   │   ├── models/
│   │   │   ├── review.py         # ReviewResult, ReviewComment
│   │   │   └── webhook_models.py # Webhook payload schemas
│   │   ├── db/
│   │   │   ├── database.py       # SQLAlchemy async engine
│   │   │   └── models.py         # ORM models
│   │   ├── services/
│   │   │   └── review_service.py # Orchestrates full flow
│   │   ├── config.py             # Settings
│   │   └── main.py               # FastAPI app
│   ├── tests/
│   ├── scripts/                  # Phase test scripts
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                     # Phase 8 React dashboard
├── docker-compose.yml
└── README.md
```
