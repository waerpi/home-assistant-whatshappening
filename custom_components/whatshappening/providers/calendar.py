"""Calendar entries that start inside the horizon.

Unlike the other sources this one is not a look at the state machine but a
service call, which for CalDAV or Google goes over the network. Appointments
do not appear from one refresh to the next, so the answer is cached for a
couple of minutes and a correspondingly longer window is fetched: whatever
slides into the horizon while the cache is warm has then already been read.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.util import dt as dt_util

from ..const import CONF_CALENDARS, KIND_CALENDAR
from ..models import UpcomingEvent
from .base import EventProvider

CACHE_TTL = timedelta(minutes=2)


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
        cached = self._cached(now, horizon_end)
        if cached is not None:
            return cached

        # Read past the horizon so the cache stays usable as it moves on.
        fetched_until = horizon_end + CACHE_TTL
        events = await self._async_fetch(now, fetched_until)
        self.memory["cache"] = {
            "fetched_at": now,
            "until": fetched_until,
            "entities": self.entities,
            "language": self.language,
            "events": events,
        }
        return list(events)

    def _cached(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent] | None:
        """The previous answer, while it still covers what is being asked."""
        cache = self.memory.get("cache")
        if cache is None:
            return None
        if now - cache["fetched_at"] >= CACHE_TTL:
            return None
        if cache["until"] < horizon_end:
            return None  # the horizon grew past what was fetched
        if cache["entities"] != self.entities or cache["language"] != self.language:
            return None
        return list(cache["events"])

    async def _async_fetch(self, now: datetime, until: datetime) -> list[UpcomingEvent]:
        response = await self.hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": self.entities,
                "start_date_time": now.isoformat(),
                "end_date_time": until.isoformat(),
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
                summary = entry.get("summary") or self.tr("calendar.untitled")
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
