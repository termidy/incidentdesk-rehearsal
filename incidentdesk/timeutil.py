"""Time helpers. Times are stored in UTC; business rules use the service time zone."""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from incidentdesk.config import settings

UTC = timezone.utc
EARLIER_FOLD_ZONES = frozenset({"Europe/Dublin", "Eire", "Africa/Casablanca", "Africa/El_Aaiun"})
LATER_GAP_ZONES = frozenset({"Europe/Chisinau", "Europe/Tiraspol"})


def service_tz():
    return ZoneInfo(settings().timezone)


def _localize(dt: datetime, tz: ZoneInfo) -> datetime:
    localized = dt.replace(tzinfo=tz)
    alternate = localized.replace(fold=1)
    if localized.utcoffset() != alternate.utcoffset():
        round_trips = (
            candidate.astimezone(UTC).astimezone(tz).replace(tzinfo=None)
            for candidate in (localized, alternate)
        )
        if all(round_trip == dt for round_trip in round_trips):
            return localized if tz.key in EARLIER_FOLD_ZONES else alternate
        if tz.key in LATER_GAP_ZONES:
            return alternate
    return localized


def now() -> datetime:
    """The current time in UTC. INCIDENTDESK_NOW pins it (demo data and tests)."""
    pinned = os.environ.get("INCIDENTDESK_NOW")
    if pinned:
        return parse_utc(pinned)
    return datetime.now(UTC)


def parse_utc(text: str) -> datetime:
    """An ISO 8601 string as an aware UTC datetime; a string without an offset is taken as UTC."""
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_local(dt: datetime) -> datetime:
    return dt.astimezone(service_tz())


def local_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """A wall-clock time in the service time zone, as an aware datetime."""
    return _localize(datetime(year, month, day, hour, minute), service_tz())


def is_business_hours(dt: datetime) -> bool:
    local = to_local(dt)
    return local.weekday() < 5 and 9 <= local.hour < 18
