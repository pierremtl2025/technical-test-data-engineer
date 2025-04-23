from dagster import DagsterExecutionStepExecutionError, OpExecutionContext, RetryPolicy, op

from moovitamix_fastapi.classes_out import ListenHistoryOut, TracksOut, UsersOut
from pipelines.helpers import _fetch_items


@op(
    name="fetch_tracks",
    description="Fetch the full list of tracks",
    retry_policy=RetryPolicy(max_retries=2, delay=5),
)
def fetch_tracks(context: OpExecutionContext) -> list[TracksOut]:
    raw = _fetch_items(context, "/tracks")
    tracks: list[TracksOut] = []
    for idx, record in enumerate(raw):
        try:
            tracks.append(TracksOut.model_validate(record))
        except Exception as err:
            context.log.error(f"Validation error for track #{idx}: {err}")
            raise DagsterExecutionStepExecutionError(f"Invalid track data at index {idx}") from err
    context.log.info(f"Fetched and validated {len(tracks)} tracks")
    return tracks


@op(
    name="fetch_users",
    description="Fetch the full list of users",
    retry_policy=RetryPolicy(max_retries=2, delay=5),
)
def fetch_users(context: OpExecutionContext) -> list[UsersOut]:
    raw = _fetch_items(context, "/users")
    users: list[UsersOut] = []
    for idx, record in enumerate(raw):
        try:
            users.append(UsersOut.model_validate(record))
        except Exception as err:
            context.log.error(f"Validation error for user #{idx}: {err}")
            raise DagsterExecutionStepExecutionError(f"Invalid user data at index {idx}") from err
    context.log.info(f"Fetched and validated {len(users)} users")
    return users


@op(
    name="fetch_listen_history",
    description="Fetch the listen‐history records",
    retry_policy=RetryPolicy(max_retries=2, delay=5),
)
def fetch_listen_history(context: OpExecutionContext) -> list[ListenHistoryOut]:
    raw = _fetch_items(context, "/listen_history")
    history: list[ListenHistoryOut] = []
    for idx, record in enumerate(raw):
        try:
            history.append(ListenHistoryOut.model_validate(record))
        except Exception as err:
            context.log.error(f"Validation error for history #{idx}: {err}")
            raise DagsterExecutionStepExecutionError(f"Invalid history data at index {idx}") from err
    context.log.info(f"Fetched and validated {len(history)} listen records")
    return history
