from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes_repo import router as repo_router
from app.api.routes_ask import router as ask_router



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(repo_router)
app.include_router(ask_router)