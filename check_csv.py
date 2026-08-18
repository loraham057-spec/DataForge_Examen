import pandas as pd
from pathlib import Path


ROOT = Path(__file__).resolve().parent

BOOKS_FILE = ROOT / "data" / "cleaned" / "books_full.csv"
GAARAAS_FILE = ROOT / "data" / "cleaned" / "gaaraas_full.csv"


def check_file(label, path, url_column):
    print()
    print("=" * 60)
    print(label)
    print("=" * 60)

    print("Fichier :", path)
    print("Existe  :", path.exists())

    if not path.exists():
        print("ERREUR : fichier introuvable.")
        return

    try:
        df = pd.read_csv(path)

        print("Lignes      :", len(df))
        print("Colonnes    :", list(df.columns))

        if url_column in df.columns:
            unique_urls = df[url_column].nunique()
            duplicates = df[url_column].duplicated().sum()

            print("URLs uniques:", unique_urls)
            print("Doublons    :", duplicates)

        print()
        print(df.head(5).to_string(index=False))

    except Exception as exc:
        print("ERREUR :", exc)


print("=" * 60)
print("VERIFICATION DES CSV DATAFORGE")
print("=" * 60)

check_file(
    "BOOKS",
    BOOKS_FILE,
    "book_url",
)

check_file(
    "GAARAAS",
    GAARAAS_FILE,
    "listing_url",
)

print()
print("=" * 60)
print("VERIFICATION TERMINEE")
print("=" * 60)