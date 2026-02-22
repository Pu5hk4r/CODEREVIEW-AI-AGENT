"""
app/models/webhook_models.py — Pydantic schemas matching GitHub webhook payloads.
"""
from typing import Optional
from pydantic import BaseModel


class GitHubUser(BaseModel):
    login: str
    id: int


class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    private: bool


class PullRequest(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: str
    user: GitHubUser
    head: dict
    base: dict
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class PullRequestEvent(BaseModel):
    action: str                  # "opened", "synchronize", "closed", ...
    number: int
    pull_request: PullRequest
    repository: GitHubRepo
    sender: GitHubUser
