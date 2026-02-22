"""
app/models/review.py — Core data models for the review pipeline.

ReviewComment → one inline code issue
ReviewResult  → full structured output from the LLM
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL   = "critical"    # Security holes, data loss, crashes
    WARNING    = "warning"     # Logic errors, performance issues
    SUGGESTION = "suggestion"  # Style, readability, best practice


class ReviewComment(BaseModel):
    file_path:   str
    line_number: Optional[int] = None  # None = general PR-level comment
    severity:    Severity
    title:       str = Field(..., description="Short title e.g. 'SQL Injection Risk'")
    body:        str = Field(..., description="Detailed explanation + how to fix")
    suggestion:  Optional[str] = None  # Corrected code snippet if applicable


class ReviewResult(BaseModel):
    summary:        str                  # One paragraph overall assessment
    comments:       list[ReviewComment]  # Individual issue list
    approved:       bool                 # Should this PR be merged?
    critical_count: int = 0
    warning_count:  int = 0
    suggestion_count: int = 0

    def model_post_init(self, __context):
        """Auto-calculate counts from comments list."""
        self.critical_count   = sum(1 for c in self.comments if c.severity == Severity.CRITICAL)
        self.warning_count    = sum(1 for c in self.comments if c.severity == Severity.WARNING)
        self.suggestion_count = sum(1 for c in self.comments if c.severity == Severity.SUGGESTION)
