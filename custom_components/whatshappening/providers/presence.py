"""Arrivals, predicted from travel-time sensors.

A travel-time sensor (Waze, Google Maps, HERE, …) whose state is the number
of minutes to get home tells us when somebody is going to arrive — but only
while they are actually away, so a person entity with a matching name vetoes
the event once they are home.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..const import CONF_TRAVEL_SENSORS, CONFIDENCE_LIKELY, KIND_PRESENCE
from ..models import UpcomingEvent
from .base import EventProvider

# Words dropped when matching a travel sensor against a person entity.
NOISE_WORDS = {
    "travel",
    "time",
    "to",
    "home",
    "nach",
    "hause",
    "fahrzeit",
    "fahrtzeit",
    "heimweg",
    "weg",
    "duration",
    "eta",
}


class PresenceProvider(EventProvider):
    """Turns travel times into "arrives at" events."""

    name = "presence"

    @property
    def entities(self) -> list[str]:
        return list(self.options.get(CONF_TRAVEL_SENSORS) or [])

    @property
    def enabled(self) -> bool:
        return bool(self.entities)

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for entity_id in self.entities:
            minutes = self.float_state(entity_id)
            if minutes is None or minutes < 0:
                continue

            traveller = self._traveller_for(entity_id)
            if traveller is not None and self._is_home(traveller):
                continue

            name = (
                self.friendly_name(traveller)
                if traveller
                else self._subject(entity_id)
            )
            events.append(
                UpcomingEvent(
                    key=f"presence:{entity_id}",
                    when=now + timedelta(minutes=minutes),
                    title=f"{name} kommt voraussichtlich nach Hause",
                    kind=KIND_PRESENCE,
                    icon="mdi:car-back",
                    emoji="🚗",
                    entity_id=entity_id,
                    detail=f"{round(minutes)} min Fahrzeit",
                    confidence=CONFIDENCE_LIKELY,
                )
            )
        return events

    # --- matching a sensor to a person ----------------------------------

    def _traveller_for(self, entity_id: str) -> str | None:
        """Best-effort match of a travel sensor to a person entity."""
        tokens = self._tokens(self.friendly_name(entity_id))
        if not tokens:
            return None

        for state in self.hass.states.async_all("person"):
            person_tokens = self._tokens(
                state.attributes.get("friendly_name") or state.entity_id
            )
            if person_tokens & tokens:
                return state.entity_id
        return None

    def _is_home(self, person_entity: str) -> bool:
        state = self.hass.states.get(person_entity)
        return state is not None and state.state == "home"

    @staticmethod
    def _tokens(value: str) -> set[str]:
        words = value.replace("_", " ").replace("-", " ").lower().split()
        return {word for word in words if word not in NOISE_WORDS and len(word) > 2}

    def _subject(self, entity_id: str) -> str:
        """Fall back to the sensor's own name, minus the boilerplate."""
        name = self.friendly_name(entity_id)
        for suffix in (" Travel Time", " Fahrzeit", " nach Hause", " to Home"):
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name
