#!/usr/bin/env python3
"""Create minimal Jupyter notebooks for the ML pipeline (Phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOKS = [
    ("01_data_exploration.ipynb", "MovieLens 25M exploration", "ml/src/data/loader.py"),
    ("02_feature_engineering.ipynb", "User and item feature construction", "ml/src/data/features.py"),
    ("03_two_tower_training.ipynb", "Two-tower training with in-batch negatives", "ml/src/training/train_two_tower.py"),
    ("04_ranker_training.ipynb", "MLP reranker with BPR loss", "ml/src/training/train_ranker.py"),
    ("05_evaluation.ipynb", "Recall@10, NDCG@10, IPS-NDCG@10", "ml/src/evaluation/metrics.py"),
]

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"


def make_notebook(title: str, module: str) -> dict:
    body = (
        f"# {title}\n\n"
        f"Implementation lives in `{module}`.\n\n"
        "For a quick end-to-end demo without MovieLens 25M, run from the repo root:\n\n"
        "```bash\npython ml/scripts/build_demo_artifacts.py\n```\n"
    )
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [body]},
        ],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, title, module in NOTEBOOKS:
        path = OUT / filename
        path.write_text(json.dumps(make_notebook(title, module), indent=2), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
