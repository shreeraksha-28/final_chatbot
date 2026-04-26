import ast
import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Primary path: same folder as this repo
_DATASET_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "tmdb_merged.csv"),
    r"C:\Users\hi\OneDrive\Desktop\chatbot\tmdb_merged.csv",
]


def _find_dataset() -> str:
    for p in _DATASET_PATHS:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            return abs_p
    raise FileNotFoundError(
        "tmdb_merged.csv not found. Checked:\n" + "\n".join(_DATASET_PATHS)
    )


def _parse_names(raw, key: str = "name") -> str:
    if not raw or (isinstance(raw, float)):
        return ""
    try:
        items = ast.literal_eval(str(raw))
        return ", ".join(item[key] for item in items if isinstance(item, dict) and key in item)
    except Exception:
        return ""


def _get_director(crew_raw) -> str:
    if not crew_raw or (isinstance(crew_raw, float)):
        return ""
    try:
        crew = ast.literal_eval(str(crew_raw))
        return ", ".join(m["name"] for m in crew if m.get("job") == "Director")
    except Exception:
        return ""


def _top_cast(cast_raw, n: int = 5) -> str:
    if not cast_raw or (isinstance(cast_raw, float)):
        return ""
    try:
        cast = ast.literal_eval(str(cast_raw))
        return ", ".join(m["name"] for m in cast[:n] if isinstance(m, dict))
    except Exception:
        return ""


def load_and_preprocess() -> pd.DataFrame:
    path = _find_dataset()
    logger.info(f"Loading dataset: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    logger.info(f"Loaded {len(df)} rows")

    df["genres_clean"] = df["genres"].apply(_parse_names)
    df["keywords_clean"] = df["keywords"].apply(_parse_names)
    df["cast_clean"] = df["cast"].apply(_top_cast)
    df["director_clean"] = df["crew"].apply(_get_director)

    for col in ["overview", "tagline", "original_title"]:
        df[col] = df[col].fillna("")

    df["combined_text"] = (
        df["original_title"] + ". "
        + df["overview"] + " "
        + "Genres: " + df["genres_clean"] + ". "
        + "Keywords: " + df["keywords_clean"] + ". "
        + "Cast: " + df["cast_clean"] + ". "
        + "Director: " + df["director_clean"] + ". "
        + "Tagline: " + df["tagline"]
    )

    df = df[df["combined_text"].str.strip() != ""].reset_index(drop=True)
    logger.info(f"Preprocessed {len(df)} valid movies")
    return df


def get_movie_metadata(row: pd.Series) -> dict:
    return {
        "title": str(row["original_title"]),
        "genres": str(row.get("genres_clean", "")),
        "vote_average": float(row.get("vote_average", 0) or 0),
        "popularity": float(row.get("popularity", 0) or 0),
        "cast": str(row.get("cast_clean", "")),
        "director": str(row.get("director_clean", "")),
        "overview": str(row["overview"])[:500],
    }
