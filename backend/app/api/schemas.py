from pydantic import BaseModel



class CreateRepoRequest(BaseModel):
    repo_url: str


class CreateRepoResponse(BaseModel):
    repo_id: str
    status: str


class RepoStatusResponse(BaseModel):
    repo_id: str
    repo_url: str
    status: str
    error: str | None = None
    chunk_count: int = 0

class AskRequest(BaseModel):
    repo_id: str
    question: str


class AskResponse(BaseModel):
    session_id: str
    status: str


class FindingOut(BaseModel):
    action: str
    target: str
    result_summary: str


class SessionResponse(BaseModel):
    session_id: str
    repo_id: str
    question: str
    status: str
    final_answer: str = ""
    findings: list[FindingOut] = []
    error: str | None = None