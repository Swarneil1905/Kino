# Kino

> **Cinema Without Compromise.** A production-grade movie recommendation system built end-to-end, from ML training through to a deployed streaming interface.

**Live demo:** https://web-production-b397d.up.railway.app
**Stack:** PyTorch · FAISS · FastAPI · PostgreSQL · Redis · Next.js 15 · Railway

---

## What this is

Kino is a full-stack recommendation system that mirrors the architecture used in production at companies like Netflix, Spotify, and YouTube. It is not a tutorial project. The ML pipeline trains a real two-tower retrieval model on MovieLens 25M, evaluates it on a held-out temporal split, reranks with an MLP layer, and applies Maximal Marginal Relevance to diversify final results. The web interface is a polished streaming UI wired to a live FastAPI backend serving sub-10ms recommendations from FAISS.

---

## Offline Evaluation Results

Evaluated on a timestamp-based 80/20 holdout split across 200 users (min 20 ratings each). Candidates retrieved via FAISS top-200 before reranking.

| Metric | Two-Tower + Ranker | + MMR (lambda=0.7) | Delta |
|--------|-------------------|--------------------|-------|
| Hit Rate@10 | 75.5% | 74.5% | -1.3% |
| NDCG@10 | 0.2160 | 0.2100 | -2.8% |
| Precision@10 | 20.5% | 19.7% | -4.0% |
| Intra-List Diversity | 0.175 | 0.246 | +40.6% |

MMR trades a modest 1-3% relevance reduction for a 40.6% gain in recommendation diversity -- the correct tradeoff for a streaming platform where filter bubbles kill long-term engagement.

---

## Architecture

```
User request
     |
     v
[ Next.js 15 Frontend ]
     |  REST
     v
[ FastAPI + uvicorn ]
     |
     +---> PostgreSQL (users, movies, ratings)
     |
     +---> Redis (rec cache TTL=15min, embedding cache TTL=1hr)
     |
     +---> Recommendation Engine
               |
               +---> UserTower (PyTorch) -> 128-dim embedding
               |
               +---> FAISS IndexFlatIP -> top-200 candidates (~2-5ms)
               |
               +---> MLP Ranker -> scored top-N pool
               |
               +---> MMR reranker (lambda=0.7) -> final 20 results
```

### ML Pipeline (`ml/`)

**Training data:** MovieLens 25M (25M ratings, 62K movies, 162K users)

**Two-Tower Model**
- User Tower: user ID embedding (256-dim) + 64-dim history encoding + 18-dim genre affinity vector -> 128-dim output
- Item Tower: item ID embedding (256-dim) + 18-dim genre vector + decade/popularity features -> 128-dim output
- Training objective: sampled softmax with in-batch negatives; cosine similarity via dot product of L2-normalized vectors
- Loss: BPR (Bayesian Personalised Ranking)

**FAISS Index**
- `IndexFlatIP` on 128-dim L2-normalized vectors (inner product = cosine similarity)
- All item embeddings pre-loaded into memory at startup; queries return top-200 in ~2-5ms
- Production path would use `IndexIVFFlat` with `nlist=256` for sub-linear scaling to millions of items

**MLP Ranker**
- Input: 387-dim feature vector (user embedding, item embedding, element-wise product, genre affinity score, log-popularity, decade)
- Two hidden layers (256 -> 128) with ReLU and dropout=0.3
- Binary cross-entropy on implicit positive (rated >= 4.0) vs sampled negatives

**Diversity Reranking**
- Maximal Marginal Relevance selects the final `k` items that jointly maximise relevance minus redundancy
- lambda=0.7 weights relevance 70% and novelty 30%
- Pairwise cosine similarity computed over pre-extracted item embeddings (loaded at startup, ~10ms overhead)

**Cold Start**
- New users: genre affinity vector built from onboarding selections, passed to UserTower with neutral user ID (0)
- Produces meaningful personalization before any ratings exist

**Evaluation**
- Temporal split: train on all ratings before timestamp median, test on after
- IPS weighting corrects for popularity bias in evaluation
- Metrics: Hit Rate@K, NDCG@K, Precision@K, Intra-List Diversity (mean pairwise cosine distance)

---

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Model training | PyTorch | Native autograd, easy custom loss functions |
| ANN search | FAISS | Industry standard; IndexFlatIP is exact at this scale |
| Diversity | MMR | Theoretically grounded, parameter-efficient |
| API | FastAPI + asyncpg | Fully async; no thread pool bottlenecks on DB queries |
| ORM | SQLAlchemy async | Type-safe, migrations via Alembic |
| Cache | Redis | TTL-based invalidation on rating events |
| Frontend | Next.js 15 App Router | RSC for initial data fetch; client components for interactivity |
| Deployment | Railway | Single-command deploy; Dockerfile for API, Nixpacks for web |

---

## Quick Start

**Prerequisites:** Docker Desktop, Node.js 20+, Python 3.11+

```bash
# Full stack
docker compose up --build

# Frontend: http://localhost:3000
# API:      http://localhost:8000
# API docs: http://localhost:8000/docs
```

**Demo accounts** (seeded automatically):

| Email | Password | Preference |
|-------|----------|------------|
| demo-scifi@kino.dev | demopass123 | Sci-Fi heavy |
| demo-action@kino.dev | demopass123 | Action heavy |
| demo-drama@kino.dev | demopass123 | Drama heavy |
| demo-animation@kino.dev | demopass123 | Animation |
| demo-mixed@kino.dev | demopass123 | Mixed genres |

**First-time flow:** Register -> `/onboarding` (rate 10 seed movies) -> personalized home -> rate more to trigger rec refresh -> `/metrics` to see offline evaluation.

---

## Project Structure

```
kino/
├── apps/
│   ├── api/                  FastAPI backend + ML inference
│   │   ├── app/
│   │   │   ├── ml/           Inference engine, FAISS, MMR, diversity
│   │   │   ├── models/       SQLAlchemy ORM models
│   │   │   ├── routers/      REST endpoints
│   │   │   └── scripts/      Seeding, data export
│   │   ├── alembic/          Database migrations
│   │   └── artifacts/        Trained model weights + FAISS index
│   └── web/                  Next.js 15 frontend
│       ├── app/              App Router pages
│       ├── components/       UI components (Navbar, HeroBanner, MovieCard)
│       └── hooks/            Data-fetching hooks
├── ml/
│   ├── src/
│   │   ├── models/           TwoTower, UserTower, ItemTower, Ranker
│   │   ├── training/         Training loops (two-tower + ranker)
│   │   ├── evaluation/       Metrics, IPS weighting
│   │   └── data/             Loaders, feature engineering, splitter
│   └── scripts/              Build artifacts, export seed data
└── .github/workflows/        CI for web (type-check, lint) and API (pytest)
```

---

## What I Would Change at Production Scale

**FAISS:** Swap `IndexFlatIP` for `IndexIVFPQ` (inverted file + product quantization). At 10M items, flat search becomes too slow; IVF with `nlist=1024` and `nprobe=64` gets recall@100 above 95% at 10x the speed.

**Retraining:** Add a daily Airflow DAG that pulls new ratings from Postgres, retrains the ranker (lighter job), and swaps FAISS index atomically with a blue/green pointer in Redis. Full two-tower retraining weekly.

**A/B testing:** Add a `variant` field to the recommendations endpoint. Route 10% of traffic to a new model version; log impression/click events to Kafka; compute lift on NDCG against the control arm.

**Feature store:** Pull user genre affinity into a Redis-backed feature store updated on every rating event, so the user embedding is always fresh without a full DB scan.

**Observability:** Emit recommendation latency, cache hit rate, and per-user diversity score to Prometheus. Alert on p99 > 50ms or hit rate drop > 5% vs 7-day rolling average.

---

## Environment Variables

| Service | Variable | Description |
|---------|----------|-------------|
| Web | `NEXT_PUBLIC_API_URL` | FastAPI base URL |
| Web | `TMDB_API_KEY` | TMDB key for poster art |
| API | `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://`) |
| API | `REDIS_URL` | Redis connection string |
| API | `SECRET_KEY` | JWT signing secret (64+ chars) |

Copy `.env.example` to `apps/api/.env` and `apps/web/.env.local`, fill in values.

---

## License

MIT
