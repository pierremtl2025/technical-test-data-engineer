import os
import time

import psycopg2
import pytest
from psycopg2 import OperationalError

from pipelines.ingest import ingest_job


@pytest.fixture(scope="module")
def postgres_conn():
    """
    Wait up to 30s for Postgres to accept connections.
    If we timeout, skip the integration tests.
    """
    db_kwargs = dict(
        dbname=os.getenv("POSTGRES_DB", "moovitamix_db"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "pwd"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
    )

    timeout_seconds = 30
    start = time.monotonic()
    while True:
        try:
            conn = psycopg2.connect(**db_kwargs)
            conn.autocommit = True
            break
        except OperationalError:
            if time.monotonic() - start > timeout_seconds:
                pytest.skip(f"Postgres not available after {timeout_seconds}s; skipping integration tests")
            time.sleep(1)

    yield conn
    conn.close()


def test_full_pipeline(postgres_conn):
    result = ingest_job.execute_in_process()
    assert result.success, "Dagster ingest_job failed to run successfully"

    with postgres_conn.cursor() as cur:
        for tbl in ("tracks", "users", "listen_history"):
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cur.fetchone()[0]
            assert count > 0, f"Expected at least one row in '{tbl}"
