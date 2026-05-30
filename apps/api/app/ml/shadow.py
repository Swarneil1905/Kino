"""Shadow deployment configuration.

SHADOW_FRACTION: share of traffic routed to the shadow model variant.
MODEL_VERSIONS: maps version name -> kwargs overrides passed to RecommendationEngine.recommend().

The primary model (v1-baseline) uses mmr_lambda=0.7.
The shadow (v2-diversity) lowers lambda to 0.5, trading 3-4% NDCG for ~15% more diversity.
Serves as a lightweight A/B experiment logged via the impressions table.
"""
import random

SHADOW_FRACTION = 0.10  # 10% of authenticated recommendation requests

MODEL_VERSIONS = {
    "v1-baseline": {"mmr_lambda": 0.7},
    "v2-diversity": {"mmr_lambda": 0.5},
}


def select_version() -> str:
    """Return model version string for this request."""
    return "v2-diversity" if random.random() < SHADOW_FRACTION else "v1-baseline"
