import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.api.reviews import router as reviews_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CodeReview AI Agent starting — env=%s", settings.app_env)
    logger.info("🤖 Using Groq model: %s", settings.groq_model)

    if settings.app_env != "test":
        try:
            from app.db.database import init_db
            await init_db()
            logger.info("✅ Database initialised")
        except Exception as e:
            logger.warning("⚠️  DB init skipped (Phase 1-4): %s", e)

    yield
    logger.info("👋 Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="CodeReview AI Agent",
        description="An AI agent that reviews Pull Requests like a senior engineer.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://codereview-ai-agent.vercel.app",
            "https://codereview-ai-agent-hz1l8kuy0-pu5hk4rs-projects.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, tags=["Health"])
    app.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
    app.include_router(reviews_router, prefix="/reviews", tags=["Reviews"])

    return app


app = create_app()