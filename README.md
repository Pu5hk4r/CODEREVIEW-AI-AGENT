# 🤖 CodeReview AI Agent

AI agent that reviews Pull Requests like a senior engineer using:
- Groq (Llama 3.1 70B)
- LangGraph
- FastAPI
- pgvector (RAG)

---
# Full Architecture
![](https://github.com/Pu5hk4r/CODEREVIEW-AI-AGENT/blob/main/GCP%20Production%20Review.png)

---

# 📊 DATA FLOW SUMMARY

1. Developer pushes bad code → opens PR on GitHub  
2. GitHub fires webhook → POST /webhook (HMAC signed)  
3. FastAPI verifies signature → returns 200 immediately  
4. Background task → starts LangGraph agent  

5. fetch_node  
   → GitHub API → gets PR diff  

6. analyze_node  
   → pgvector → retrieves similar code chunks  

7. review_node  
   → Groq API → structured JSON review  

8. post_node  
   → GitHub API → posts comments on PR  

9. post_node  
   → PostgreSQL → saves review permanently  

10. Dashboard  
   → GET /reviews → shows all past reviews  

---

---

# ☁️ GCP DEPLOYMENT ARCHITECTURE

GitHub → Cloud Run → Cloud SQL (Postgres + pgvector)

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
- Never stored in code or Dockerfile

External Services:
- Groq API
- GitHub API

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
# 🧪 TESTING STRATEGY (PHASE-WISE)

Phase 1 → test_phase1.py  — server health  
Phase 2 → test_phase2.py  — webhook signature  
Phase 3 → manual          — Groq response  
Phase 4 → manual          — agent pipeline  
Phase 5 → check_db.py     — database tables  
Phase 6 → real GitHub PR  — end-to-end  
Phase 7 → check_db.py     — data persistence  
Phase 8 → browser         — dashboard UI  

---
# 🔁 END-TO-END FLOW

PR opened on GitHub  
→ Webhook received  
→ Agent completed all 4 nodes  
→ Comment posted on PR  
→ Review saved in PostgreSQL  
→ Dashboard shows review  

---

# 🧪 MANUAL TESTING (REAL PR)

Step 1:
Created auth.py with vulnerabilities:
- SQL injection (line 5)
- Hardcoded secret (line 1)
- No DB connection close

Step 2:
Pushed to feature/bad-code-v2 branch  

Step 3:
Opened PR on GitHub  

Step 4:
Verified webhook received (ngrok logs)  

Step 5:
Verified agent ran all nodes (server logs)  

Step 6:
Verified Groq detected SQL injection  

Step 7:
Verified comment on PR  

Step 8:
Verified review saved in PostgreSQL  

Step 9:
Verified dashboard data  

---

# 📈 PERFORMANCE METRICS

## Latency Metrics

Webhook receive + return 200  → <100ms  
GitHub fetch PR diff          → 2–3s  
RAG retrieval                 → <100ms  
Groq inference                → 2–5s  
GitHub post comment           → 1–2s  
PostgreSQL save               → <500ms  

TOTAL end-to-end              → ~30–60s  

---

## Throughput Metrics

Groq free tier limit: 30 req/min  
Usage: 1 review per PR  
Max PRs/hour: ~30  

---

## Accuracy Metrics

Test PRs: 3  
Issues planted: 4  
Issues found: 3/4 (75%)

- SQL Injection → Found  
- Hardcoded Secret → Found  
- No DB close → Found  
- Input validation → Missed  

Precision: 100%  
Recall: 75%  

---

## Reliability Metrics

Webhooks received: 5  
Processed: 5  

Reviews completed: 3  
Failures: 0  

DB saves: 3/3  
GitHub posts: 3/3  

---

# ✅ FUNCTIONAL EVALUATION

- Webhook receive → Yes  
- Signature verification → Yes  
- Agent execution → Yes  
- Issue detection → Yes (75%)  
- PR comments → Yes  
- DB persistence → Yes  
- Dashboard → Yes  

---

# 🧠 LLM OUTPUT QUALITY

- Correct severity classification  
- Accurate line numbers  
- Actionable fixes  
- No hallucinations  

---

# 🧪 PROMPT EVALUATION

V1 → vague output  
V2 → structured but inconsistent  
V3 → strict JSON → stable + accurate  

---

# ⚠️ ERROR HANDLING

- Empty PR → handled  
- Wrong webhook secret → 401  
- Malformed JSON → logged  
- Async issues → fixed  
- Port conflict → resolved  
- Uppercase severity → normalized  

---

# 📊 SYSTEM RELIABILITY MONITORING

Monitored:
- Server logs
- ngrok logs
- PostgreSQL data
- GitHub comments  

Log levels:
- INFO  
- WARNING  
- ERROR  

---

# 🧪 AUTOMATED TEST SUITE

tests/
- test_webhook.py
- test_agent.py
- test_groq.py
- test_github.py
- test_db.py
- test_e2e.py

---

# ☁️ GCP MONITORING

- Request latency
- Error rate
- CPU/memory usage

Custom metrics:
- Reviews/hour
- Critical issues/day
- Avg review time  

---

# 🧠 LLM EVALUATION FRAMEWORK

Dataset:
- 20 PRs with known issues  

Metrics:
- Precision  
- Recall  
- F1 Score  
- Hallucination rate  

Current:
- Precision: 100%  
- Recall: 75%  

---


# ⚙️ Environment Variables

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

# 🏃 Quick Start

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
