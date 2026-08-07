from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalise a DB datetime to timezone-aware UTC.

    Columns are declared `DateTime(timezone=True)`, but SQLite has no native
    timezone support and hands back *naive* datetimes — so any arithmetic mixing
    a stored value with `datetime.now(timezone.utc)` raises TypeError under the
    test suite while working fine on Postgres. Everything that compares against
    a stored timestamp must go through here.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
