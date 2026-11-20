from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.store import (
    get_repo,
    create_session,
    get_session,
    finish_session,
    fail_session,
)
from app.api.schemas import AskRequest, AskResponse, SessionResponse
from app.agent.graph import build_graph
from app.store import update_session_findings

router = APIRouter(prefix="/ask", tags=["ask"])


_graph = build_graph()


def run_agent_task(session_id: str, repo_id: str, question: str):
    try:
        initial_state = {
            "repo_id": repo_id,
            "question": question,
            "findings": [],
            "steps_taken": 0,
            "next_action": {},
            "confident_enough": False,
            "final_answer": "",
        }
        final_state = initial_state
        for state in _graph.stream(initial_state, config={"recursion_limit": 50}, stream_mode="values"):
            final_state = state
            update_session_findings(session_id, state["findings"])
        finish_session(session_id, final_state["final_answer"], final_state["findings"])
    except Exception as e:
        fail_session(session_id, str(e))


@router.post("", response_model=AskResponse)
def ask(payload: AskRequest, background_tasks: BackgroundTasks):
    repo = get_repo(payload.repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="repo not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"repo is not ready (status: {repo.status})")

    session = create_session(payload.repo_id, payload.question)
    background_tasks.add_task(run_agent_task, session.id, session.repo_id, session.question)
    return AskResponse(session_id=session.id, status=session.status)


@router.get("/{session_id}", response_model=SessionResponse)
def get_answer(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return SessionResponse(
        session_id=session.id,
        repo_id=session.repo_id,
        question=session.question,
        status=session.status,
        final_answer=session.final_answer,
        findings=session.findings,
        error=session.error,
    )

