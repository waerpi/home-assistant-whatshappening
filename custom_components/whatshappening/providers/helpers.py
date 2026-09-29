"""Helper-entity providers: schedules, timers and input_datetime."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.util import dt as dt_util

from ..const import (
    CONF_ENABLE_INPUT_DATETIME,
    CONF_ENABLE_SCHEDULES,
    CONF_ENABLE_TIMERS,
    KIND_DATETIME,
    KIND_SCHEDULE,
    KIND_TIMER,
)
from ..models import UpcomingEvent
from .base import EventProvider


class ScheduleProvider(EventProvider):
    """`schedule.*` helpers publish their next switch in `next_event`."""

    name = "schedule"

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLE_SCHEDULES, True))

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for state in self.hass.states.async_all("schedule"):
            raw = state.attributes.get("next_event")
            if not raw:
                continue
            when = dt_util.parse_datetime(str(raw))
            if when is None:
                continue
            turning_on = state.state == "off"
            name = self.friendly_name(state.entity_id)
            events.append(
                UpcomingEvent(
                    key=f"schedule:{state.entity_id}",
                    when=dt_util.as_local(when),
                    title=self.tr(
                        "schedule.starts" if turning_on else "schedule.ends",
                        name=name,
                    ),
                    kind=KIND_SCHEDULE,
                    icon="mdi:calendar-clock",
                    emoji="🗓",
                    entity_id=state.entity_id,
                )
            )
        return events


class TimerProvider(EventProvider):
    """Running `timer.*` helpers finish at a known point in time."""

    name = "timer"

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLE_TIMERS, True))

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for state in self.hass.states.async_all("timer"):
            if state.state != "active":
                continue
            raw = state.attributes.get("finishes_at")
            if not raw:
                continue
            when = dt_util.parse_datetime(str(raw))
            if when is None:
                continue
            events.append(
                UpcomingEvent(
                    key=f"timer:{state.entity_id}",
                    when=dt_util.as_local(when),
                    title=self.tr(
                        "timer.finished", name=self.friendly_name(state.entity_id)
                    ),
                    kind=KIND_TIMER,
                    icon="mdi:timer-outline",
                    emoji="⏲",
                    entity_id=state.entity_id,
                )
            )
        return events


class InputDatetimeProvider(EventProvider):
    """`input_datetime` helpers that point at a moment in the near future."""

    name = "input_datetime"

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLE_INPUT_DATETIME, True))

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for state in self.hass.states.async_all("input_datetime"):
            timestamp = state.attributes.get("timestamp")
            if timestamp is None:
                continue
            when = self._resolve(now, state.attributes, float(timestamp))
            events.append(
                UpcomingEvent(
                    key=f"input_datetime:{state.entity_id}",
                    when=when,
                    title=self.friendly_name(state.entity_id),
                    kind=KIND_DATETIME,
                    icon="mdi:clock-outline",
                    emoji="⏰",
                    entity_id=state.entity_id,
                )
            )
        return events

    @staticmethod
    def _resolve(now: datetime, attributes: dict, timestamp: float) -> datetime:
        """Turn the helper's timestamp into an absolute local datetime.

        With a date part the timestamp is a normal epoch value; without one
        it counts seconds into the day and therefore repeats daily.
        """
        if attributes.get("has_date", True):
            return dt_util.as_local(dt_util.utc_from_timestamp(timestamp))

        candidate = dt_util.start_of_local_day(now) + timedelta(seconds=timestamp)
        if candidate < now:
            candidate += timedelta(days=1)
        return candidate
