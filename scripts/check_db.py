import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

# Ensure src/ is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pwd@localhost:5432/moovitamix_db")


def fetch_first_rows(table: str, limit: int = 1) -> pd.DataFrame:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        return pd.read_sql(
            text(f"SELECT * FROM {table} LIMIT :limit"),
            conn,
            params={"limit": limit},
        )


def main():
    tables = ["tracks", "users", "listen_history"]
    for tbl in tables:
        print(f"\n=== First rows of `{tbl}` ===")
        df = fetch_first_rows(tbl, limit=5)
        if df.empty:
            print("(no rows)")
        else:
            print(df.to_string(index=False))
    print()


if __name__ == "__main__":
    main()
