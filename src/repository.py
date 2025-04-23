from dagster import repository

from pipelines.ingest import ingest_job
from pipelines.schedules import daily_ingest_schedule


@repository
def moovitamix_ingestion():
    return [
        ingest_job,
        daily_ingest_schedule,
    ]
