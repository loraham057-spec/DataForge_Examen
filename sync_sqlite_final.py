from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "database" / "data_collection.db"
BOOKS = ROOT / "data" / "cleaned" / "books_full.csv"
GAARAAS = ROOT / "data" / "cleaned" / "gaaraas_full.csv"


def replace_table(conn, table_name, csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)

    # Remplacement complet :
    # les anciennes lignes ne sont pas conservées.
    df.to_sql(
        table_name,
        conn,
        if_exists="replace",
        index=False,
    )

    return len(df)


def main():
    print("=" * 70)
    print("DATAFORGE - SYNCHRONISATION SQLITE")
    print("=" * 70)

    if not DB.exists():
        raise FileNotFoundError(DB)

    conn = sqlite3.connect(DB)

    try:
        books_count = replace_table(
            conn,
            "books",
            BOOKS,
        )

        gaaraas_count = replace_table(
            conn,
            "gaaraas",
            GAARAAS,
        )

        conn.commit()

    finally:
        conn.close()

    print()
    print(f"books   = {books_count:,} lignes")
    print(f"gaaraas = {gaaraas_count:,} lignes")
    print()
    print("SQLite synchronisée par remplacement complet.")
    print("=" * 70)


if __name__ == "__main__":
    main()
