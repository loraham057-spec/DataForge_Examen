from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_books_contract():
    df = pd.read_csv(ROOT / "data/cleaned/books_clean.csv")
    required = {"title", "price", "availability", "products_count", "rating", "reviews", "description", "category", "tax"}
    assert required.issubset(df.columns)
    assert len(df) == 1000
    assert df["book_url"].is_unique


def test_gaaraas_contract():
    df = pd.read_csv(ROOT / "data/cleaned/gaaraas_clean.csv")
    required = {"brand", "model", "year", "price", "mileage", "gearbox", "region"}
    assert required.issubset(df.columns)
    assert len(df) == 245
    assert df["listing_url"].is_unique
