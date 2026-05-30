# Kino: End-to-End Neural Recommendation System
### Technical Design Document

**Author:** Swarneil Pradhan
**Live system:** https://web-production-b397d.up.railway.app
**Code:** https://github.com/Swarneil1905/Kino

---

## Problem

Recommendation systems at streaming platforms face a core tension: pure relevance maximization leads to filter bubbles. A user who watches three action movies gets action movies forever, engagement peaks briefly, then collapses as novelty disappears. The goal was to build a system that produces accurate, diverse recommendations -- and to measure the tradeoff between those two objectives rigorously.

---

## Architecture Decisions

**Why two-tower retrieval over matrix factorization?**

Matrix factorization (ALS, SVD++) is effective but couples user and item representations. At inference time you can only retrieve by dot product against a fixed user embedding -- you cannot incorporate fresh signals like a genre filter or session context. The two-tower architecture separates the user and item encoders, which means the item index can be built once and queried with any user vector, including cold-start genre vectors for new users.

**Why FAISS over a vector database like Pinecone?**

For 3,000-15,000 items, `IndexFlatIP` runs in ~2-5ms on CPU with exact results. Pinecone adds network latency and cost for a scale that doesn't warrant it. The code uses `IndexFlatIP` now but the inference module is structured so that swapping to `IndexIVFPQ` at 10M items requires changing two lines.

**Why MMR over beam search or portfolio optimization for diversity?**

MMR (Maximal Marginal Relevance) has a closed-form greedy solution and a single interpretable hyperparameter (lambda). At each step it selects the item that maximizes `lambda * relevance - (1-lambda) * max_similarity_to_selected`. At lambda=0.7 the 40% diversity gain at a 2.8% NDCG cost is a deliberate product decision: marginal relevance loss is acceptable, filter-bubble elimination is not optional. A production system would tune lambda per user cohort via A/B test.

**Why IPS weighting in evaluation?**

MovieLens ratings are missing not at random. Users rate movies they sought out, which skews toward popular items. An unweighted evaluator would show inflated metrics for a popularity-biased model. IPS (Inverse Propensity Scoring) weights each observation by the inverse likelihood it was observed, correcting for selection bias. The propensity scores are estimated from item rating frequency.

---

## Results

Evaluated on a temporal 80/20 holdout split (200 users, min 20 ratings each, candidates retrieved from FAISS top-200).

| Metric | Ranker only | + MMR |
|--------|------------|-------|
| Hit Rate@10 | 75.5% | 74.5% |
| NDCG@10 | 0.216 | 0.210 |
| Precision@10 | 20.5% | 19.7% |
| Intra-List Diversity | 0.175 | 0.246 |

The Hit Rate@10 of 75.5% means the model surfaces at least one movie the user actually rated highly in 3 out of 4 top-10 lists. NDCG@10 of 0.216 reflects the ranking quality -- not just presence but position. These numbers are meaningful, not cherry-picked: the temporal split ensures the test set represents future behavior, not retrospective fits.

---

## Cold Start

New users have no rating history. Instead of falling back to pure popularity (the standard approach), the onboarding flow collects genre preferences and builds an 18-dimensional genre affinity vector. This vector is passed directly to the UserTower with a neutral user ID. The model produces a meaningful embedding -- not random noise, not a global average -- because the UserTower learned from thousands of users with those genre affinities during training.

---

## What I Would Change at Scale

Three things stand out as genuine production gaps.

**Retraining pipeline.** Currently the model is trained once. At scale, rating events would stream to Kafka, a daily Airflow job would retrain the MLP ranker (faster), and a weekly job would retrain the full two-tower. The FAISS index would swap atomically via a Redis pointer, with a 5-minute blue/green overlap.

**Online feature freshness.** User genre affinity is computed from all historical ratings at inference time (a DB scan). This is fine at hundreds of users but breaks at millions. The correct architecture is a Redis-backed feature store that updates the affinity vector on every rating event, so the recommendation endpoint reads a pre-computed vector in microseconds.

**A/B testing.** The recommendations endpoint has no concept of variants. Adding a `variant` flag in the response header, logging impressions and clicks to a Kafka topic, and running a holdout test measuring 7-day engagement lift would close the gap between offline evaluation (which I have) and online evaluation (which is what actually matters in production).

---

## Engineering choices worth noting

The API is fully async (asyncpg, SQLAlchemy async engine, FastAPI). There are no thread pool bottlenecks on database queries -- every route is a coroutine. The recommendation cache uses a 15-minute TTL in Redis, invalidated immediately on a rating event so the user sees updated recommendations after interaction. The FAISS index and model weights are loaded once at startup into process memory via FastAPI's lifespan context; recommendation latency is effectively FAISS search time plus one Postgres query.
