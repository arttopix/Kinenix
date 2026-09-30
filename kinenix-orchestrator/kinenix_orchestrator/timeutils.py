"""Timestamp handling for the Orchestrator.

Timestamps are stored as naive UTC datetimes, because SQLite drops timezone
information, and are serialized with an explicit +00:00 offset so browsers
convert them to the viewer's local time correctly.
"""
import datetime
from typing import Optional


def utc_now() -> datetime.datetime:
    """Current time as naive UTC, for storage."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def to_utc_naive(value: datetime.datetime) -> datetime.datetime:
    """Convert a datetime to naive UTC for storage.

    A naive input is assumed to be in the Orchestrator host's local time, which
    matches older kinenix-core releases that sent local time without an offset.
    """
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def parse_timestamp(value: Optional[str]) -> Optional[datetime.datetime]:
    """Parse an ISO 8601 timestamp from a worker payload into naive UTC. Returns None if absent or invalid."""
    if not value:
        return None
    text = str(value).strip()
    if text.endswith(("Z", "z")):
        # datetime.fromisoformat() only accepts a Z suffix from Python 3.11
        text = text[:-1] + "+00:00"
    try:
        return to_utc_naive(datetime.datetime.fromisoformat(text))
    except ValueError:
        return None


def isoformat_utc(value: Optional[datetime.datetime]) -> Optional[str]:
    """Serialize a stored naive UTC datetime as ISO 8601 with a +00:00 offset."""
    if value is None:
        return None
    return value.replace(tzinfo=datetime.timezone.utc).isoformat()
