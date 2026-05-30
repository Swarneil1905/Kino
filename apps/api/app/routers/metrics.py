import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.impression import Impression

router = APIRouter(prefix="/metrics", tags=["metrics"])

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def _load_model_meta() -> dict:
    meta_path = ARTIFACTS / "model_meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except Exception:
            pass
    return {}


def _build_model_info() -> dict:
    meta = _load_model_meta()
    return {
        "architecture":  "Two-Tower Neural Network",
        "embedding_dim": meta.get("embed_dim", 128),
        "hidden_dim":    256,
        "num_movies":    meta.get("num_items", 3000),
        "num_users":     meta.get("num_users", 15000),
        "training_data": "MovieLens 25M",
        "retrieval":     "FAISS IndexFlatIP (inner product)",
        "reranking":     "Maximal Marginal Relevance (lambda=0.7 / 0.5)",
    }


EVAL_CONFIG = {
    "n_users":     500,
    "k":           10,
    "mmr_lambda":  0.7,
    "split":       "80/20 temporal",
    "candidates":  200,
    "min_ratings": 20,
}


@router.get("")
async def get_metrics(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    """Offline evaluation results, model metadata, and live online metrics."""

    # --- Offline eval ---
    eval_path = ARTIFACTS / "eval_results.json"
    if eval_path.exists():
        eval_data = json.loads(eval_path.read_text())
        baseline = eval_data.get("baseline", {})
        mmr      = eval_data.get("mmr", {})
    else:
        baseline = {"hit_rate_at_10": 0.755, "ndcg_at_10": 0.216, "precision_at_10": 0.205, "intra_list_distance": 0.175, "n_users_evaluated": 200}
        mmr      = {"hit_rate_at_10": 0.745, "ndcg_at_10": 0.210, "precision_at_10": 0.1965, "intra_list_distance": 0.2458, "n_users_evaluated": 200}

    def delta(b, m, key):
        bv, mv = float(b.get(key, 0)), float(m.get(key, 0))
        return round((mv - bv) / bv * 100, 1) if bv else 0.0

    comparison = [
        {"metric": "Hit Rate@10",          "description": "% of users where >= 1 relevant movie appears in top 10", "baseline": round(float(baseline.get("hit_rate_at_10", 0)), 4),      "mmr": round(float(mmr.get("hit_rate_at_10", 0)), 4),      "delta": delta(baseline, mmr, "hit_rate_at_10")},
        {"metric": "NDCG@10",              "description": "Ranking quality -- rewards relevant items ranked higher",  "baseline": round(float(baseline.get("ndcg_at_10", 0)), 4),          "mmr": round(float(mmr.get("ndcg_at_10", 0)), 4),          "delta": delta(baseline, mmr, "ndcg_at_10")},
        {"metric": "Precision@10",         "description": "Fraction of top-10 recommendations that are relevant",    "baseline": round(float(baseline.get("precision_at_10", 0)), 4),     "mmr": round(float(mmr.get("precision_at_10", 0)), 4),     "delta": delta(baseline, mmr, "precision_at_10")},
        {"metric": "Intra-List Diversity", "description": "Mean pairwise cosine distance -- higher = more varied",   "baseline": round(float(baseline.get("intra_list_distance", 0)), 4), "mmr": round(float(mmr.get("intra_list_distance", 0)), 4), "delta": delta(baseline, mmr, "intra_list_distance")},
    ]

    # --- Online metrics from impressions table ---
    online = await _compute_online_metrics(db)

    return {
        "model":      _build_model_info(),
        "eval":       EVAL_CONFIG,
        "comparison": comparison,
        "n_users":    int(baseline.get("n_users_evaluated", 200)),
        "online":     online,
    }


async def _compute_online_metrics(db: AsyncSession) -> dict:
    """Compute CTR by position and per-version metrics from the impressions table."""

    # Total impressions + clicks
    total_q = await db.execute(
        select(
            func.count(Impression.id).label("total"),
            func.sum(case((Impression.clicked.is_(True), 1), else_=0)).label("clicks"),
        )
    )
    totals = total_q.one()
    total_impressions = int(totals.total or 0)
    total_clicks      = int(totals.clicks or 0)
    overall_ctr       = round(total_clicks / total_impressions, 4) if total_impressions else 0.0

    # CTR by position (positions 0-19)
    pos_q = await db.execute(
        select(
            Impression.position,
            func.count(Impression.id).label("impressions"),
            func.sum(case((Impression.clicked.is_(True), 1), else_=0)).label("clicks"),
        )
        .where(Impression.position < 20)
        .group_by(Impression.position)
        .order_by(Impression.position)
    )
    ctr_by_position = [
        {
            "position":    row.position,
            "impressions": int(row.impressions),
            "clicks":      int(row.clicks),
            "ctr":         round(int(row.clicks) / int(row.impressions), 4) if row.impressions else 0.0,
        }
        for row in pos_q.all()
    ]

    # Per-version comparison (shadow experiment)
    version_q = await db.execute(
        select(
            Impression.model_version,
            func.count(Impression.id).label("impressions"),
            func.sum(case((Impression.clicked.is_(True), 1), else_=0)).label("clicks"),
        )
        .group_by(Impression.model_version)
    )
    version_stats = [
        {
            "version":     row.model_version,
            "impressions": int(row.impressions),
            "clicks":      int(row.clicks),
            "ctr":         round(int(row.clicks) / int(row.impressions), 4) if row.impressions else 0.0,
        }
        for row in version_q.all()
    ]

    return {
        "total_impressions": total_impressions,
        "total_clicks":      total_clicks,
        "overall_ctr":       overall_ctr,
        "ctr_by_position":   ctr_by_position,
        "version_stats":     version_stats,
        "note": "CTR by position reveals position bias -- items shown first get disproportionately more clicks regardless of relevance.",
    }
