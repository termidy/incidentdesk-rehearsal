"""The shift table of a rotation, for the on-call page."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from incidentdesk.oncall.schedule import ROTATIONS, handoff_before, on_call
from incidentdesk.timeutil import _localize


@dataclass(frozen=True)
class Shift:
    engineer: str
    starts_at: datetime
    ends_at: datetime


def shifts(rotation_name: str, start: datetime, weeks: int) -> list[Shift]:
    """`weeks` shifts of the rotation, from the shift that covers `start`. Times are in the rotation's time zone."""
    rotation = ROTATIONS[rotation_name]
    tz = ZoneInfo(rotation.timezone)
    handoff = handoff_before(rotation, start)
    table = []
    for _ in range(weeks):
        # a week later in wall time, localized again: the handoff stays at 10:00 across a daylight saving change
        nxt = _localize(handoff.replace(tzinfo=None) + timedelta(days=7), tz)
        table.append(Shift(on_call(rotation_name, handoff), handoff, nxt))
        handoff = nxt
    return table
