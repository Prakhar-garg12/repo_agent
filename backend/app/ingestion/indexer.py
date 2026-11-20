import uuid
from typing import List

from sentence_transformers import SentenceTransformer
from qdrant_client.http import models as qmodels

from app.ingestion.parser import CodeChunk
from app.vectorstore import upsert_chunks


_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    return _model.encode([text])[0].tolist()


BATCH = 64


def index_chunks(repo_id: str, chunks: List[CodeChunk]) -> int:

    total = 0
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        # the model only reads the first ~256 tokens anyway
        vectors = _model.encode([c.content[:2000] for c in batch]).tolist()

        points = [
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "repo_id": repo_id,
                    "file_path": chunk.file_path,
                    "content": chunk.content[:4000],
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                },
            )
            for chunk, vector in zip(batch, vectors)
        ]
        upsert_chunks(points)
        total += len(points)
        print(f"indexed {total}/{len(chunks)}")

    return total