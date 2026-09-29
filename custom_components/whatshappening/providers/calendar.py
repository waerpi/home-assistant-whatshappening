"""Calendar entries that start inside the horizon."""

from __future__ import annotations

from datetime import datetime

from homeassistant.util import dt as dt_util

from ..const import CONF_CALENDARS, KIND_CALENDAR
from ..models import UpcomingEvent
from .base import EventProvider


class CalendarProvider(EventProvider):
    """Reads the configured calendar entities via `calendar.get_events`."""

    name = "calendar"

    @property
    def entities(self) -> list[str]:
        return list(self.options.get(CONF_CALENDARS) or [])

    @property
    def enabled(self) -> bool:
        return bool(self.entities)

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        response = await self.hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": self.entities,
                "start_date_time": now.isoformat(),
                "end_date_time": horizon_end.isoformat(),
            },
            blocking=True,
            return_response=True,
        )
        if not response:
            return []

        events: list[UpcomingEvent] = []
        for entity_id, payload in response.items():
            for entry in payload.get("events", []):
                when = self._start_of(entry)
                if when is None:
                    continue
                summary = entry.get("summary") or "Termin"
                events.append(
                    UpcomingEvent(
                        key=f"calendar:{entity_id}:{summary}:{when.isoformat()}",
                        when=when,
                        title=summary,
                        kind=KIND_CALENDAR,
                        icon="mdi:calendar",
                        emoji="📅",
                        entity_id=entity_id,
                        detail=entry.get("location") or self.friendly_name(entity_id),
                    )
                )
        return events

    @staticmethod
    def _start_of(entry: dict) -> datetime | None:
        """All-day entries carry a plain date, timed entries a datetime."""
        raw = entry.get("start")
        if not raw:
            return None
        parsed = dt_util.parse_datetime(str(raw))
        if parsed is None:
            date = dt_util.parse_date(str(raw))
            if date is None:
                return None
            parsed = dt_util.start_of_local_day(date)
        return dt_util.as_local(parsed)
