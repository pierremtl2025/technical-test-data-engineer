from dagster import ScheduleDefinition

from pipelines.ingest import ingest_job

daily_ingest_schedule = ScheduleDefinition(
    job=ingest_job,
    cron_schedule="0 8 * * *",
    execution_timezone="America/Toronto",
    name="daily_ingest_schedule",
    should_execute=lambda _context: True,
    description="Daily at 8 AM run of local_ingest_job",
)
