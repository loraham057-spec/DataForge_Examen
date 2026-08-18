"""SQLite persistence for the Data Collection exam project."""
from pathlib import Path
import sqlite3
import pandas as pd


def database_path(root: Path) -> Path:
    path = root / "data" / "database"
    path.mkdir(parents=True, exist_ok=True)
    return path / "data_collection.db"


def connect(root: Path) -> sqlite3.Connection:
    return sqlite3.connect(database_path(root))


def init_database(root: Path) -> None:
    with connect(root) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS database_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                application TEXT NOT NULL,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO database_info(id, application, description)
            VALUES (1, 'Data Collection Exam',
                    'SQL storage for Books to Scrape and Gaaraas')
            """
        )


def sync_dataset(root: Path, source: str, csv_path: Path) -> int:
    table = {"books": "books", "gaaraas": "gaaraas"}.get(source)
    if not table:
        raise ValueError("Source SQL inconnue")
    df = pd.read_csv(csv_path)
    init_database(root)
    with connect(root) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)
        conn.execute(
            "UPDATE database_info SET updated_at=CURRENT_TIMESTAMP WHERE id=1"
        )
    return len(df)


def read_table(root: Path, table: str) -> pd.DataFrame:
    if table not in {"books", "gaaraas"}:
        raise ValueError("Table SQL non autorisée")
    init_database(root)
    with connect(root) as conn:
        return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)


def table_count(root: Path, table: str) -> int:
    try:
        return int(read_table(root, table).shape[0])
    except Exception:
        return 0


def list_tables(root: Path) -> list[str]:
    init_database(root)
    with connect(root) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [r[0] for r in rows]
