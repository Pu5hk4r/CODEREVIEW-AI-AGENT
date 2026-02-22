"""
app/api/reviews.py — REST endpoints for past review data.

PHASE 7 CHECKPOINT:
  GET /reviews      → list all past PR reviews
  GET /reviews/{id} → single review with comments
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Phase 1-6: in-memory store (replaced by DB in Phase 7) ──────────────────
_review_store: list = []


def add_review_to_store(review_data: dict):
    """Called by ReviewService after each completed review."""
    _review_store.append(review_data)


@router.get("")
async def list_reviews(
    repo: Optional[str] = Query(None, description="Filter by repo full_name"),
    limit: int = Query(20, le=100),
):
    """List past PR reviews (most recent first)."""
    reviews = list(reversed(_review_store))
    if repo:
        reviews = [r for r in reviews if r.get("repo_name") == repo]
    return {"reviews": reviews[:limit], "total": len(reviews)}


@router.get("/{review_id}")
async def get_review(review_id: str):
    """Get a single review by ID."""
    for review in _review_store:
        if review.get("id") == review_id:
            return review
    raise HTTPException(status_code=404, detail="Review not found")


@router.get("/health/store")
async def store_health():
    """Quick check on in-memory store size."""
    return {"reviews_in_memory": len(_review_store)}
