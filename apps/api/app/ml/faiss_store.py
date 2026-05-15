from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


class FaissStore:
    def __init__(self) -> None:
        self.index: faiss.IndexFlatIP | None = None
        self.movie_id_map: dict[int, int] = {}

    def load(self) -> bool:
        index_path = ARTIFACTS_DIR / "faiss_index.bin"
        map_path = ARTIFACTS_DIR / "movie_id_map.json"
        if not index_path.exists() or not map_path.exists():
            return False
        self.index = faiss.read_index(str(index_path))
        raw = json.loads(map_path.read_text())
        self.movie_id_map = {int(pos): int(mid) for pos, mid in raw.items()}
        return True

    def search(self, embedding: np.ndarray, k: int = 200) -> list[int]:
        if self.index is None:
            return []
        vec = embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(vec)
        _, indices = self.index.search(vec, min(k, self.index.ntotal))
        return [self.movie_id_map[int(i)] for i in indices[0] if int(i) >= 0]
