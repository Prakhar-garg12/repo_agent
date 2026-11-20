import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

MAX_FILE_BYTES = 200_000   
MAX_CHUNKS = 2500          

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "target", "vendor", ".tox", ".mypy_cache",
    ".pytest_cache", ".next", "coverage", "site-packages",
}

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rb", ".md"}


@dataclass
class CodeChunk:
    file_path: str
    content: str
    start_line: int
    end_line: int


def parse_repo(repo_path: Path) -> List[CodeChunk]:
    candidates = []

    for dirpath, dirnames, filenames in os.walk(repo_path):

        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix not in SOURCE_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            rel = path.relative_to(repo_path)

            candidates.append((path.suffix == ".md", len(rel.parts), rel.as_posix(), path))

    candidates.sort()
    kept = candidates[:MAX_CHUNKS]
    print(f"parser: kept {len(kept)} of {len(candidates)} candidate files")

    chunks: List[CodeChunk] = []
    for _, _, rel, path in kept:
        content = path.read_text(errors="ignore")
        chunks.append(
            CodeChunk(
                file_path=rel,
                content=content,
                start_line=1,
                end_line=content.count("\n") + 1,
            )
        )
    return chunks