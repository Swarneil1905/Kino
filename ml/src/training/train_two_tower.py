"""Train two-tower model on MovieLens 25M. Run: python -m ml.src.training.train_two_tower"""

from __future__ import annotations

from pathlib import Path

from ml.scripts.build_demo_artifacts import main

if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[2] / "data"
    if (data_dir / "ratings.csv").exists():
        print("Full MovieLens training: implement in notebook 03_two_tower_training.ipynb")
    else:
        print("No MovieLens data found; building demo artifacts from synthetic data.")
        main()
