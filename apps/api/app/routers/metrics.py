import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/metrics", tags=["metrics"])

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


@router.get("")
async def get_metrics() -> dict[str, float | str]:
    path = ARTIFACTS / "eval_metrics.json"
    if path.exists():
        return json.loads(path.read_text())
    return {
        "recall_at_10": 0.0,
        "ndcg_at_10": 0.0,
        "ips_ndcg_at_10": 0.0,
        "model_version": "untrained-dev",
    }
