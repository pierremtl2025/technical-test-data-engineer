from dagster import ScheduleDefinition

from pipelines.ingest import ingest_job
from pipelines.schedules import daily_ingest_schedule


def test_schedule_definition_attributes():
    assert isinstance(daily_ingest_schedule, ScheduleDefinition)

    assert daily_ingest_schedule.name == "daily_ingest_schedule"
    assert daily_ingest_schedule.cron_schedule == "0 8 * * *"
    assert daily_ingest_schedule.execution_timezone == "America/Toronto"
    assert daily_ingest_schedule.job_name == ingest_job.name
