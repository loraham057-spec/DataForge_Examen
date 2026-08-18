import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "data" / "database" / "data_collection.db"


print("=" * 60)
print("VERIFICATION SQLITE DATAFORGE")
print("=" * 60)

print(f"Base    : {DB_PATH}")
print(f"Existe  : {DB_PATH.exists()}")

if not DB_PATH.exists():
    print()
    print("ERREUR : base SQLite introuvable.")
    raise SystemExit(1)


try:
    conn = sqlite3.connect(DB_PATH)

    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    print()
    print(f"Nombre de tables : {len(tables)}")
    print()

    for table_tuple in tables:
        table_name = table_tuple[0]

        count = conn.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        print(f"{table_name} = {count:,} lignes")

    conn.close()

except sqlite3.Error as exc:
    print()
    print(f"ERREUR SQLITE : {exc}")
    raise SystemExit(1)


print()
print("=" * 60)
print("VERIFICATION TERMINEE")
print("=" * 60)