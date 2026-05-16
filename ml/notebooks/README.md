# Kino ML Notebooks

Jupyter notebooks for the MovieLens 25M training pipeline:

1. `01_data_exploration.ipynb` — dataset statistics and rating distributions
2. `02_feature_engineering.ipynb` — user/item feature construction
3. `03_two_tower_training.ipynb` — two-tower training with in-batch negatives
4. `04_ranker_training.ipynb` — MLP reranker with BPR loss
5. `05_evaluation.ipynb` — Recall@10, NDCG@10, IPS-NDCG@10

Run `python ml/scripts/build_demo_artifacts.py` from the repo root to generate demo artifacts without the full dataset.

Regenerate notebook stubs with `python ml/scripts/generate_notebooks.py`.
