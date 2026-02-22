# 🤖 CodeReview AI Agent

An AI agent that reviews Pull Requests like a senior engineer — powered by **Groq** (Llama 3.1 70B), **LangGraph**, **FastAPI**, and **pgvector RAG**.

---

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
