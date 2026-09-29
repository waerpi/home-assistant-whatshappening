"""Sunrise, sunset, dawn and dusk from the built-in `sun.sun` entity."""

from __future__ import annotations

from datetime import datetime

from homeassistant.util import dt as dt_util

from ..const import CONF_ENABLE_SUN, KIND_SUN
from ..models import UpcomingEvent
from .base import EventProvider

# attribute -> (title, emoji, icon)
SUN_EVENTS = {
    "next_rising": ("Sonnenaufgang", "🌄", "mdi:weather-sunset-up"),
    "next_setting": ("Sonnenuntergang", "🌅", "mdi:weather-sunset-down"),
    "next_dawn": ("Morgendämmerung", "🌆", "mdi:weather-sunset-up"),
    "next_dusk": ("Abenddämmerung", "🌇", "mdi:weather-sunset-down"),
    "next_noon": ("Sonnenhöchststand", "☀️", "mdi:weather-sunny"),
}


class SunProvider(EventProvider):
    """Solar events — always exact, never a guess."""

    name = "sun"

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLE_SUN, True))

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        state = self.state_of("sun.sun")
        if state is None:
            return []

        events: list[UpcomingEvent] = []
        for attribute, (title, emoji, icon) in SUN_EVENTS.items():
            raw = state.attributes.get(attribute)
            if not raw:
                continue
            when = dt_util.parse_datetime(str(raw))
            if when is None:
                continue
            events.append(
                UpcomingEvent(
                    key=f"sun:{attribute}",
                    when=dt_util.as_local(when),
                    title=title,
                    kind=KIND_SUN,
                    icon=icon,
                    emoji=emoji,
                    entity_id="sun.sun",
                )
            )
        return events
