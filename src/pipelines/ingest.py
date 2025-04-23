from dagster import graph

from .extract import fetch_listen_history, fetch_tracks, fetch_users
from .load import load_to_postgres


@graph
def ingest_graph():
    tracks = fetch_tracks()
    users = fetch_users()
    history = fetch_listen_history()
    load_to_postgres(tracks, users, history)


ingest_job = ingest_graph.to_job(name="local_ingest_job")
