# Model Card — Kino Recommendation System

## Model Details

| Field | Value |
|-------|-------|
| Name | Kino Two-Tower Retrieval + MLP Ranker |
| Version | v1-baseline (production) / v2-diversity (10% shadow) |
| Type | Neural collaborative filtering — two-tower retrieval with learned re-ranking |
| Framework | PyTorch 2.x |
| Training data | MovieLens 25M (GroupLens Research, University of Minnesota) |
| Embedding dimension | 128 |
| Retrieval index | FAISS IndexFlatIP (exact inner product search) |
| Diversity layer | Maximal Marginal Relevance (MMR) |
| Inference latency | ~8-15ms p50 (FAISS + ranker + MMR on CPU) |
| Maintained by | Swarneil Pradhan |
| Last trained | May 2026 |

---

## Intended Use

**Primary use case:** Personalised movie recommendations for authenticated users of the Kino streaming interface.

**Out-of-scope uses:**
- Recommendations for minors (no age-filtering logic exists)
- High-stakes decisions (hiring, lending, medical)
- Any domain outside entertainment content discovery
- Real-time fraud detection or safety-critical systems

---

## Training Data

**Source:** [MovieLens 25M](https://grouplens.org/datasets/movielens/25m/) — 25 million ratings applied to 62,423 movies by 162,541 users between January 1995 and November 2019.

**Licence:** Available for non-commercial research and education use.

**Split:** Temporal 80/20 — all ratings before the median timestamp form the training set; ratings after form the test set. This simulates predicting future user behaviour, not retrospective pattern-matching.

**Label definition:** Implicit positive = rating >= 4.0 (out of 5). Ratings below 4.0 are treated as negatives during ranker training.

### Known Data Biases

**Popularity bias.** MovieLens ratings are heavily skewed toward popular titles. A user who rates 20 movies will predominantly have rated well-known films. The model will therefore recommend popular titles more frequently than niche ones, even for users with niche preferences. Mitigation: IPS (Inverse Propensity Scoring) weighting during offline evaluation corrects for this in metrics; MMR diversity reranking mitigates it at serving time.

**Western / English-language overrepresentation.** The MovieLens 25M catalog skews heavily toward Hollywood productions and English-language content. Users whose genuine preferences align with non-English cinema (Bollywood, Korean, Japanese) will receive lower-quality recommendations. The genre encoder includes `Animation` as a proxy for anime but does not have a dedicated international cinema signal.

**Survivorship bias.** The dataset only contains movies that received enough ratings to appear in the catalog. Films released after November 2019 are absent. Recent releases (2020-present) cannot be recommended by the trained model — they are absent from the FAISS index entirely.

**Temporal drift.** User taste changes over time. A rating from 2005 is treated identically to one from 2019. The model has no decay weighting on older interactions.

**Rating scale ambiguity.** A 4-star rating means different things to different users. No user-level normalisation is applied (e.g., mean-centring).

---

## Evaluation

### Methodology

- **Split:** Timestamp-based 80/20 holdout (not random split, which would inflate metrics)
- **Population:** 200 users with at least 20 ratings each
- **Candidate retrieval:** FAISS top-200 per user, then ranker scoring
- **Bias correction:** IPS weighting using item rating frequency as propensity proxy

### Offline Results

| Metric | Two-Tower + Ranker | + MMR (lambda=0.7) | Delta |
|--------|-------------------|--------------------|-------|
| Hit Rate@10 | 75.5% | 74.5% | -1.3% |
| NDCG@10 | 0.216 | 0.210 | -2.8% |
| Precision@10 | 20.5% | 19.7% | -4.0% |
| Intra-List Diversity | 0.175 | 0.246 | +40.6% |

MMR trades ~2-3% relevance for a 40% diversity improvement — the intended product tradeoff.

### Online Metrics (live)

The system logs every recommendation impression to the `impressions` table (user_id, movie_id, position, model_version, shown_at, clicked). The `/metrics` API endpoint computes:

- **Overall CTR** — clicks / impressions across all positions
- **CTR by position** — quantifies position bias (position 0 receives disproportionate clicks regardless of item quality)
- **Per-version CTR** — compares v1-baseline (lambda=0.7) vs v2-diversity (lambda=0.5) under 10% shadow traffic

Position bias in CTR is expected and documented, not a model failure. Debiased evaluation would require a randomisation experiment (showing items in random order for a holdout group).

---

## Shadow Deployment (A/B Infrastructure)

10% of authenticated recommendation requests are served by **v2-diversity** (MMR lambda=0.5 — more diverse, slightly less precise). Both variants log to the impressions table with their version string. This enables CTR comparison between versions without a separate experiment framework.

**v1-baseline:** lambda=0.7 (70% relevance, 30% novelty)
**v2-diversity:** lambda=0.5 (50% relevance, 50% novelty)

Promotion of v2-diversity to primary requires: (a) statistically significant CTR lift over 7+ days, (b) no regression in NDCG on a fresh offline eval, (c) manual review of recommendation samples for quality.

---

## Limitations

1. **No retraining pipeline.** The model is trained once. User taste drift, new movie releases, and distribution shift are not corrected. A production deployment would retrain the ranker daily and the full two-tower weekly.

2. **Cold-start approximation.** New users receive recommendations based on a genre affinity vector with a neutral user ID (0). This is better than pure popularity but worse than a model that has seen the user's actual behaviour.

3. **No content safety filtering.** The model does not filter for age-appropriate content, sensitive topics, or user-specified content preferences. Any downstream deployment must add explicit filtering.

4. **Single language.** The recommendation signal is implicit ratings only — no natural language understanding of title, overview, or review text. Semantic similarity between items is approximated by genre and popularity features only.

5. **Scale assumptions.** FAISS IndexFlatIP is exact but O(n) in index size. Above ~500k items, IVF or HNSW indexing is required to maintain sub-10ms latency.

---

## Responsible Deployment Requirements

Any production deployment beyond this portfolio context would require:

- Age-gating and content maturity filtering before any recommendation serves
- User-facing controls: "Not interested," content category blocks, data deletion
- A privacy review of the impression logging schema (user_id + movie_id + timestamp is behavioural data requiring consent under GDPR / CCPA)
- Bias audit across demographic proxies (genre preference distributions as a proxy for cultural background)
- Regular retraining with data freshness monitoring
- An oncall rotation with alerting on recommendation quality degradation (CTR drop > 15% vs 7-day baseline)

---

## Citation

F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. *ACM Transactions on Interactive Intelligent Systems (TiiS)* 5, 4: 19:1-19:19.
