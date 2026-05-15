# Kino

A Netflix-style movie recommendation web application powered by a two-tower neural retrieval model, FAISS vector search, and an MLP reranker. Built as a portfolio project demonstrating end-to-end ML engineering.

## Architecture

```text
Next.js (apps/web)
  └── FastAPI (apps/api)
        ├── PostgreSQL — users, movies, ratings
        ├── Redis — recommendation & embedding cache
        ├── PyTorch two-tower model — user/item embeddings
        ├── FAISS IndexFlatIP — approximate nearest neighbor retrieval
        └── MLP ranker — rescores top-200 candidates
```

### ML Pipeline

1. **Two-tower model** — User and item towers map to a shared 128-dim space; similarity is dot product of L2-normalized vectors (cosine similarity).
2. **FAISS retrieval** — All item embeddings indexed with `IndexFlatIP`; queries return top-200 candidates in ~2–5ms.
3. **Ranking layer** — 387-dim MLP reranker scores candidates using user/item embeddings, element-wise product, genre affinity, and popularity features.
4. **Evaluation** — Recall@10, NDCG@10, and IPS-weighted NDCG@10 on a timestamp-based holdout split.

Training code lives in `ml/`. Run `python ml/scripts/build_demo_artifacts.py` to generate demo artifacts (full MovieLens 25M training uses `ml/src/training/train_two_tower.py` when data is present in `ml/data/`).

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local API dev)

### Full stack with Docker

**Windows:** If `docker` is not recognized, Docker Desktop is not installed or not on your PATH. Run:

```powershell
.\scripts\check-docker.ps1
```

Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/), reboot, wait until Docker Desktop shows **Engine running**, then open a **new** terminal:

```powershell
docker compose up --build
```

### Local dev without Docker

If you cannot use Docker yet, install PostgreSQL locally and run:

```powershell
.\scripts\start-local.ps1
```

Follow the printed commands in two terminals (API + web).

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local development

**API**

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Start PostgreSQL and Redis (or use docker compose up postgres redis)
uvicorn main:app --reload
```

**Web**

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

### First-time user flow

1. Register at `/register`
2. Complete onboarding — rate 10 seed movies at `/onboarding`
3. Browse personalized rows on the home screen
4. Rate more movies from expanded cards to refresh recommendations
5. View model metrics at `/metrics`

### Demo accounts

After the API starts, five demo users are seeded automatically (or run `python -m app.scripts.seed_demo_accounts` from `apps/api`):

| Email | Password |
|-------|----------|
| `demo-scifi@kino.dev` | `demopass123` |
| `demo-action@kino.dev` | `demopass123` |
| `demo-drama@kino.dev` | `demopass123` |
| `demo-animation@kino.dev` | `demopass123` |
| `demo-mixed@kino.dev` | `demopass123` |

### Database migrations

```bash
cd apps/api
alembic upgrade head
```

Docker runs migrations automatically via `entrypoint.sh` before starting uvicorn.

## Project Structure

```text
kino/
├── apps/web/          Next.js 14 frontend
├── apps/api/          FastAPI backend + ML inference
├── ml/                Training pipeline & artifacts
├── .github/workflows/ CI for web and API
└── docker-compose.yml
```

## Environment Variables

| Service | Variable | Description |
|---------|----------|-------------|
| Web | `NEXT_PUBLIC_API_URL` | FastAPI base URL |
| Web | `TMDB_API_KEY` | Optional TMDB key for richer metadata |
| API | `DATABASE_URL` | PostgreSQL async connection string |
| API | `REDIS_URL` | Redis connection string |
| API | `SECRET_KEY` | JWT signing secret (64+ chars in production) |

## Deployment (Railway)

Deploy three services in one Railway project: API (Docker), PostgreSQL, Redis, and Web (Nixpacks). Set `NEXT_PUBLIC_API_URL` to the API service URL. Bundle ML artifacts in `apps/api/app/artifacts/` before building the API image.

## License

MIT
