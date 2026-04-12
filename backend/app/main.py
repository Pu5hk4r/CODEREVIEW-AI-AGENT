"""
app/main.py — FastAPI application factory.

PHASE 1 CHECKPOINT: uvicorn app.main:app --reload
  → GET http://localhost:8000/health should return {"status": "ok"}
  → GET http://localhost:8000/docs should show Swagger UI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.api.reviews import router as reviews_router

settings = get_settings()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CodeReview AI Agent starting — env=%s", settings.app_env)
    logger.info("🤖 Using Groq model: %s", settings.groq_model)

    # Phase 5+: init DB tables
    if settings.app_env != "test":
        try:
            from app.db.database import init_db
            await init_db()
            logger.info("✅ Database initialised")
        except Exception as e:
            logger.warning("⚠️  DB init skipped (Phase 1-4): %s", e)

    yield
    logger.info("👋 Shutting down")


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="CodeReview AI Agent",
        description=(
            "An AI agent that reviews Pull Requests like a senior engineer "
            "— powered by Groq (Llama 3.1 70B) and LangGraph."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allow dashboard (Phase 8)
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["http://localhost:5173", 
    #                    "http://localhost:3000",
    #                    "https://codereview-ai-agent-hz1l8kuy0-pu5hk4rs-projects.vercel.app"
    #                    "https://codereview-ai-agent.vercel.app",
    #                    ],
    #     allow_credentials = True,              
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, tags=["Health"])
    app.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
    app.include_router(reviews_router, prefix="/reviews", tags=["Reviews"])

    return app


app = create_app()
