import os

import pandas as pd
from dagster import op
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import DateTime

from moovitamix_fastapi.classes_out import ListenHistoryOut, TracksOut, UsersOut


@op
def load_to_postgres(
    context,
    tracks: list[TracksOut],
    users: list[UsersOut],
    listen_history: list[ListenHistoryOut],
):
    # Build engine
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:pwd@localhost:5432/moovitamix_db",
    )
    engine = create_engine(db_url)

    # Need to specify some data types because pandas handles the other types
    data_map = {
        "tracks": pd.DataFrame([t.model_dump() for t in tracks]),
        "users": pd.DataFrame([u.model_dump() for u in users]),
        "listen_history": pd.DataFrame([h.model_dump() for h in listen_history]),
    }

    # Ensure `items` is always a list
    if not data_map["listen_history"]["items"].empty:
        data_map["listen_history"]["items"] = data_map["listen_history"]["items"].apply(lambda x: x or [])

    dtype_map = {
        "tracks": {"created_at": DateTime(), "updated_at": DateTime()},
        "users": {"created_at": DateTime(), "updated_at": DateTime()},
        "listen_history": {
            "created_at": DateTime(),
            "updated_at": DateTime(),
            "items": JSONB(),  # because `items` is a list
        },
    }

    # Load data per table
    for table_name, df in data_map.items():
        try:
            df.to_sql(
                table_name,
                engine,
                if_exists="replace",
                index=False,
                dtype=dtype_map[table_name],
            )
            context.log.info(f"Loaded {len(df)} rows into '{table_name}'")
        except Exception as err:
            context.log.error(f"Failed to load '{table_name}': {err}")
            raise
