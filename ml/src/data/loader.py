from pathlib import Path

import pandas as pd


def load_movielens(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(data_dir)
    ratings_path = root / "ratings.csv"
    movies_path = root / "movies.csv"

    if not ratings_path.exists() or not movies_path.exists():
        raise FileNotFoundError("Expected ratings.csv and movies.csv in ml/data")

    ratings = pd.read_csv(ratings_path)
    movies = pd.read_csv(movies_path)
    return ratings, movies
