# Kino

A Netflix-style movie recommendation system built end-to-end -- from raw MovieLens 25M data through a trained two-tower neural network to a production-ready web app. Built as a portfolio project demonstrating full ML engineering: data pipelines, model training, vector search, REST API, and a polished frontend.

## Demo accounts

| Email | Password |
|-------|----------|
| `demo-scifi@kino.dev` | `demopass123` |
| `demo-action@kino.dev` | `demopass123` |
| `demo-drama@kino.dev` | `demopass123` |
| `demo-animation@kino.dev` | `demopass123` |
| `demo-mixed@kino.dev` | `demopass123` |

---

## Architecture

```
Browser
  └── Next.js 14 (App Router)
        └── FastAPI
              ├── PostgreSQL  -- users, movies, ratings
              ├── Redis       -- recommendation cache
              ├── PyTorch two-tower model
              ├── FAISS IndexFlatIP (ANN retrieval)
              └── MMR reranker (diversity)
```

### ML pipeline

**1. Data -- MovieLens 25M**
Filtered to the 3,000 most-rated movies and up to 15,000 users (minimum 20 ratings each). Ratings are split per-user by timestamp: 80% train, 20% test. This prevents data leakage and simulates real deployment conditions.

**2. Feature engineering**
Each user gets a genre affinity vector built from their training ratings -- liked genres get positive weight, disliked genres get a small negative penalty, then L1-normalised. Each item gets a genre one-hot vector and numeric features (release decade, log-popularity).

**3. Two-tower model**
A UserTower and ItemTower each produce 128-dimensional L2-normalised embeddings. The user tower takes a user ID, a 64-dim history embedding, and the genre affinity vector. The item tower takes an item ID, genre vector, and numeric features. Trained with in-batch softmax cross-entropy (InfoNCE-style) using AdamW and a cosine LR schedule for 10 epochs.

**4. FAISS retrieval**
All 3,000 item embeddings are indexed with `IndexFlatIP`. At inference, the user embedding is searched against the index to retrieve the top-200 candidates via approximate nearest-neighbour inner product search.

**5. MMR reranking**
The top-200 candidates are reranked using Maximal Marginal Relevance (lambda=0.7), which iteratively selects the next item that best balances relevance score and diversity from already-selected items.

**6. Cold-start**
New users with no ratings are shown a genre picker. Selected genres build a synthetic affinity vector fed directly into the UserTower, producing personalised results before any ratings exist.

### Offline evaluation

Evaluated on 491 held-out MovieLens users (80/20 temporal split):

| Metric | Baseline | With MMR | Change |
|--------|----------|----------|--------|
| Hit Rate@10 | 0.1405 | 0.1548 | +10.2% |
| NDCG@10 | 0.0252 | 0.0264 | +4.8% |
| Precision@10 | 0.0202 | 0.0216 | +6.9% |
| Intra-List Diversity | 0.0668 | 0.1236 | +85.0% |

MMR improves all four metrics simultaneously -- the diversity reranking surfaces relevant items that pure cosine similarity ranks too conservatively.

---

## Project structure

```
kino/
├── apps/
│   ├── web/               Next.js 14 frontend
│   └── api/               FastAPI backend + inference engine
│       └── app/
│           ├── routers/   auth, movies, ratings, recommendations, metrics
│           ├── models/    SQLAlchemy ORM models
│           └── artifacts/ trained weights + FAISS index (baked into Docker image)
├── ml/
│   ├── src/
│   │   ├── models/        two_tower.py, user_tower.py, item_tower.py
│   │   ├── data/          features.py, splitter.py, loader.py
│   │   └── evaluation/    metrics.py, ips_weighting.py
│   ├── scripts/
│   │   ├── train_movielens.py      full training pipeline
│   │   ├── evaluate.py             offline eval (--compare runs baseline vs MMR)
│   │   ├── enrich_tmdb.py          fetch TMDB posters for seed data
│   │   └── update_db_movies.py     upsert movies into Postgres
│   └── data/              MovieLens 25M CSVs (not committed)
├── docker-compose.yml
└── .github/workflows/     CI for web and API
```

---

## Quick start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ with a virtual environment (for ML scripts)
- Node.js 20+ (only for local frontend development outside Docker)

### Run with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Metrics: http://localhost:3000/metrics

Database migrations run automatically on startup. The five demo accounts above are seeded on first run.

### Local API development

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
# PostgreSQL and Redis must be running (docker compose up postgres redis)
uvicorn main:app --reload
```

### Local frontend development

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

---

## Retraining

Download MovieLens 25M from https://grouplens.org/datasets/movielens/25m/ and place the CSVs in `ml/data/`. Then from the kino root:

```bash
# Train (writes artifacts to ml/artifacts/ and apps/api/app/artifacts/)
python -m ml.scripts.train_movielens

# Evaluate
python -m ml.scripts.evaluate --compare --n 500

# Fetch TMDB posters for the new movie set
python ml/scripts/enrich_tmdb.py

# Upsert movies into Postgres
python ml/scripts/update_db_movies.py

# Rebuild the API container to pick up new artifacts
docker compose up -d --build api
```

---

## Environment variables

| Service | Variable | Description |
|---------|----------|-------------|
| Web | `NEXT_PUBLIC_API_URL` | FastAPI base URL (default: http://localhost:8000) |
| Web | `TMDB_READ_TOKEN` | TMDB read access token for poster images |
| API | `DATABASE_URL` | PostgreSQL async connection string |
| API | `REDIS_URL` | Redis connection string |
| API | `SECRET_KEY` | JWT signing secret (64+ random chars in production) |

---

## License

MIT
