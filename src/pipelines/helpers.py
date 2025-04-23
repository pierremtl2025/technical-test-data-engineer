import os

import requests
from dagster import DagsterExecutionStepExecutionError, OpExecutionContext

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def _fetch_items(
    context: OpExecutionContext,
    path: str,
    timeout_seconds: int = 10,
) -> list[dict]:
    """
    Helper to GET {API_BASE}{path}, validate status, parse JSON,
    and extract the "items" list.
    """
    url = f"{API_BASE}{path}"
    context.log.debug(f"Fetching from {url} (timeout={timeout_seconds}s)")
    try:
        resp = requests.get(url, timeout=timeout_seconds)
        resp.raise_for_status()
    except requests.RequestException as err:
        context.log.error(f"API error fetching {url}: {err}")
        raise DagsterExecutionStepExecutionError(f"Failed to fetch {url}") from err

    try:
        payload = resp.json()
    except ValueError as err:
        context.log.error(f"Invalid JSON returned from {url}: {err}")
        raise DagsterExecutionStepExecutionError(f"Invalid JSON from {url}") from err

    items = payload.get("items", [])
    if not isinstance(items, list):
        context.log.warning(f"Expected a list under 'items' at {url}, got {type(items)}; defaulting to []")
        items = []

    return items
