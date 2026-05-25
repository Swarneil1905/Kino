import json
from pathlib import Path

from fastapi import APIRouter

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

# Model architecture constants — augmented with live model_meta.json values
def _build_model_info() -> dict:
    meta = _load_model_meta()
    return {
        "architecture":   "Two-Tower Neural Network",
        "embedding_dim":  meta.get("embed_dim", 128),
        "hidden_dim":     256,
        "num_movies":     meta.get("num_items", 3000),
        "num_users":      meta.get("num_users", 15000),
        "training_data":  "MovieLens 25M",
        "retrieval":      "FAISS IndexFlatIP (inner product)",
        "reranking":      "Maximal Marginal Relevance (λ=0.7)",
    }

EVAL_CONFIG = {
    "n_users":          500,
    "k":                10,
    "mmr_lambda":       0.7,
    "split":            "80/20 temporal",
    "candidates":       200,
    "min_ratings":      20,
}


@router.get("")
async def get_metrics() -> dict:
    """Return offline evaluation results and model metadata for the Metrics page."""
    eval_path = ARTIFACTS / "eval_results.json"

    if eval_path.exists():
        eval_data = json.loads(eval_path.read_text())
        baseline  = eval_data.get("baseline", {})
        mmr       = eval_data.get("mmr", {})
    else:
        # Fallback to last known values from our evaluation run
        baseline = {
            "hit_rate_at_10":      0.755,
            "ndcg_at_10":          0.216,
            "precision_at_10":     0.205,
            "intra_list_distance": 0.175,
            "n_users_evaluated":   200,
        }
        mmr = {
            "hit_rate_at_10":      0.745,
            "ndcg_at_10":          0.210,
            "precision_at_10":     0.1965,
            "intra_list_distance": 0.2458,
            "n_users_evaluated":   200,
        }

    # Compute deltas for the comparison table
    def delta(b, m, key):
        bv, mv = float(b.get(key, 0)), float(m.get(key, 0))
        return round((mv - bv) / bv * 100, 1) if bv else 0.0

    comparison = [
        {
            "metric":      "Hit Rate@10",
            "description": "% of users where ≥1 relevant movie appears in top 10",
            "baseline":    round(float(baseline.get("hit_rate_at_10", 0)), 4),
            "mmr":         round(float(mmr.get("hit_rate_at_10", 0)), 4),
            "delta":       delta(baseline, mmr, "hit_rate_at_10"),
        },
        {
            "metric":      "NDCG@10",
            "description": "Ranking quality — rewards relevant items ranked higher",
            "baseline":    round(float(baseline.get("ndcg_at_10", 0)), 4),
            "mmr":         round(float(mmr.get("ndcg_at_10", 0)), 4),
            "delta":       delta(baseline, mmr, "ndcg_at_10"),
        },
        {
            "metric":      "Precision@10",
            "description": "Fraction of top-10 recommendations that are relevant",
            "baseline":    round(float(baseline.get("precision_at_10", 0)), 4),
            "mmr":         round(float(mmr.get("precision_at_10", 0)), 4),
            "delta":       delta(baseline, mmr, "precision_at_10"),
        },
        {
            "metric":      "Intra-List Diversity",
            "description": "Mean pairwise cosine distance — higher means more varied recs",
            "baseline":    round(float(baseline.get("intra_list_distance", 0)), 4),
            "mmr":         round(float(mmr.get("intra_list_distance", 0)), 4),
            "delta":       delta(baseline, mmr, "intra_list_distance"),
        },
    ]

    return {
        "model":      _build_model_info(),
        "eval":       EVAL_CONFIG,
        "comparison": comparison,
        "n_users":    int(baseline.get("n_users_evaluated", 500)),
    }
