# Repo Onboarding Agent

Paste a GitHub repository, ask a question about it, and watch an AI agent explore the codebase (listing folders, reading files, and searching code) to answer you. Every claim in the answer is tied back to a file the agent actually read.

## Features

- **Agentic exploration**: a LangGraph loop of planner → explorer → confidence check → synthesizer, with a cap of 8 exploration steps per question.
- **Three tools**: `list_dir`, `read_file` (chunked reads for long files) and `search_code` (semantic search).
- **Semantic code search**: files are embedded with `all-MiniLM-L6-v2` and stored in Qdrant.
- **Grounded answers**: the synthesizer must cite the file behind each statement, lists unsupported points under "Not verified", and appends a coverage note for files it only partly read.
- **Live repository map**: the frontend draws the repo as an interactive D3 tree and shows the agent's path through it as it works.
- **Resilient LLM calls**: automatic retries on rate limits, connection errors and invalid JSON.

## How it works

1. **Ingest**: `POST /repos` clones the repo (shallow, single branch), parses source files, embeds them and upserts them into Qdrant. Status moves through `cloning → parsing → indexing → ready`.
2. **Ask**: `POST /ask` starts a background agent session. The agent plans an action, runs it, checks whether it knows enough, and repeats until confident (or the step limit is reached).
3. **Answer**: the synthesizer writes the final answer from the collected findings. The frontend polls `GET /ask/{session_id}` to show progress and the result.

## Tech stack

| Layer | Tools |
| --- | --- |
| API | FastAPI, Uvicorn, Pydantic Settings |
| Agent | LangGraph, OpenAI SDK pointed at Google's Gemini OpenAI-compatible endpoint |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 384 dimensions) |
| Vector DB | Qdrant (via Docker) |
| Git | GitPython |
| Frontend | Vanilla JS, D3, marked, DOMPurify |

## Project structure

```
repo_agent/
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py            # FastAPI app, CORS, /health
│       ├── config.py          # Settings loaded from .env
│       ├── store.py           # In-memory repo and session records
│       ├── vectorstore.py     # Qdrant client helpers
│       ├── agent/
│       │   ├── graph.py       # LangGraph nodes and LLM calls
│       │   ├── prompts.py     # Planner, confidence, synthesizer prompts
│       │   ├── state.py       # Agent state types
│       │   └── tools.py       # list_dir, read_file, search_code
│       ├── api/
│       │   ├── routes_repo.py # Repo ingestion, status, tree
│       │   ├── routes_ask.py  # Ask questions, fetch answers
│       │   └── schemas.py     # Request/response models
│       └── ingestion/
│           ├── cloner.py      # Shallow git clone
│           ├── parser.py      # File discovery and chunking
│           └── indexer.py     # Embedding and Qdrant upsert
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── docker-compose.yml         # Qdrant
```

## Prerequisites

- Python 3.11+
- Docker (for Qdrant)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/Prakhar-garg12/repo_agent.git
cd repo_agent
```

### 2. Start Qdrant

```bash
docker compose up -d
```

Qdrant will be available at `http://localhost:6333`.

### 3. Set up the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
pip install openai langgraph
```

Create `backend/.env`:

```env
GEMINI_API_KEY=your_key_here
```

Optional settings (defaults shown):

```env
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
WORKSPACE_DIR=
ALLOWED_ORIGINS=["http://localhost:3000"]
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

The first run downloads the embedding model, so startup may take a moment.

### 4. Serve the frontend

In a new terminal:

```bash
cd frontend
python -m http.server 3000
```

Open [http://localhost:3000](http://localhost:3000), paste a GitHub URL, click **Load**, and start asking questions.

> The frontend calls the API at `http://localhost:8000` (set at the top of `frontend/app.js`), and the backend only allows requests from `http://localhost:3000` by default. Keep those ports, or update both.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/repos` | Submit a repo for ingestion. Body: `{"repo_url": "..."}` |
| `GET` | `/repos/{repo_id}/status` | Ingestion status and chunk count |
| `GET` | `/repos/{repo_id}/tree` | Flat file tree used by the map view |
| `POST` | `/ask` | Ask a question. Body: `{"repo_id": "...", "question": "..."}` |
| `GET` | `/ask/{session_id}` | Session status, findings so far, and final answer |

Example:

```bash
curl -X POST http://localhost:8000/repos \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/pallets/click"}'
```

Interactive docs are available at `http://localhost:8000/docs`.

## Limitations

- **In-memory state**: repo and session records are lost when the server restarts.
- **Indexing limits**: only `.py`, `.js`, `.ts`, `.java`, `.go`, `.rb` and `.md` files under 200 KB are indexed, up to 2,500 files per repo. Common folders like `node_modules`, `.git` and `venv` are skipped.
- **Whole-file chunks**: each file is embedded as a single chunk, and only roughly the first 256 tokens influence the embedding.
- **Public repos only**: cloning uses plain `git clone` with no authentication.

## License

Add a license of your choice.
