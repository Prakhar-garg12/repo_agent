import uuid
from typing import Optional, Literal
from datetime import datetime, timezone



RepoStatus = Literal[
    "pending", 
    "cloning", 
    "parsing", 
    "indexing", 
    "ready", 
    "failed",
]



class RepoRecord:
    def __init__(self, repo_url: str):
        self.id: str = str(uuid.uuid4())
        self.repo_url: str = repo_url
        self.status: RepoStatus = "pending"
        self.error: Optional[str] = None
        self.chunk_count: int = 0
        self.created_at: datetime = datetime.now(timezone.utc)

# In-memory storage
_repos: dict[str, RepoRecord] = {}


def create_repo(repo_url: str) -> RepoRecord:

    if not repo_url:
        raise ValueError("Repository URL cannot be empty")
    
    record = RepoRecord(repo_url)
    _repos[record.id] = record
    return record


def get_repo(repo_id: str) -> Optional[RepoRecord]:
    return _repos.get(repo_id)


def update_repo_status(repo_id: str, status: RepoStatus, error: Optional[str] = None) -> None:
    record = _repos.get(repo_id)
    if record is None:
        raise ValueError(f"Repository not found: {repo_id}")
    
    record.status = status
    record.error = error

def set_chunk_count(repo_id: str, count: int) -> None:

    if count < 0:
        raise ValueError("Chunk count cannot be negative")
    
    record = _repos.get(repo_id)

    if record is None:
        raise ValueError(f"Repository not found: {repo_id}")
    
    record.chunk_count = count




SessionStatus = Literal["running", "done", "failed"]


class SessionRecord:
    def __init__(self, repo_id: str, question: str):
        self.id: str = str(uuid.uuid4())
        self.repo_id: str = repo_id
        self.question: str = question
        self.status: SessionStatus = "running"
        self.final_answer: str = ""
        self.findings: list = []
        self.error: Optional[str] = None
        self.created_at: datetime = datetime.now(timezone.utc)


_sessions: dict[str, SessionRecord] = {}


def create_session(repo_id: str, question: str) -> SessionRecord:
    record = SessionRecord(repo_id, question)
    _sessions[record.id] = record
    return record


def get_session(session_id: str) -> Optional[SessionRecord]:
    return _sessions.get(session_id)


def finish_session(session_id: str, final_answer: str, findings: list) -> None:
    record = _sessions.get(session_id)
    if record is None:
        raise ValueError(f"Session not found: {session_id}")
    record.status = "done"
    record.final_answer = final_answer
    record.findings = findings


def fail_session(session_id: str, error: str) -> None:
    record = _sessions.get(session_id)
    if record is None:
        raise ValueError(f"Session not found: {session_id}")
    record.status = "failed"
    record.error = error

def update_session_findings(session_id: str, findings: list) -> None:
    record = _sessions.get(session_id)
    if record is not None:
        record.findings = list(findings)