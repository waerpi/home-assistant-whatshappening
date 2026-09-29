"""Base class shared by all event providers."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import HomeAssistant, State

from ..localization import format_number, translate
from ..models import UpcomingEvent

_LOGGER = logging.getLogger(__name__)


class EventProvider:
    """Collects upcoming events from one source of truth.

    A provider never raises: a broken or missing source must not take the
    whole timeline down, so `async_collect` swallows and logs errors.
    """

    name: str = "provider"

    def __init__(self, hass: HomeAssistant, options: dict, memory: dict) -> None:
        self.hass = hass
        self.options = options
        # Scratch space that survives between refreshes — providers that
        # learn from observation (appliance runtimes, sensor trends) keep
        # their samples here, namespaced by provider name.
        self.memory = memory.setdefault(self.name, {})

    @property
    def enabled(self) -> bool:
        return True

    async def async_collect(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        if not self.enabled:
            return []
        try:
            events = await self.async_get_events(now, horizon_end)
        except Exception:  # noqa: BLE001 - one bad source must not break the rest
            _LOGGER.exception("Provider %s failed to collect events", self.name)
            return []
        return [event for event in events if now <= event.when <= horizon_end]

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        raise NotImplementedError

    # --- localization ---------------------------------------------------

    @property
    def language(self) -> str:
        """The language Home Assistant is set to, read fresh each refresh."""
        return self.hass.config.language

    def tr(self, key: str, **placeholders: object) -> str:
        return translate(self.language, key, **placeholders)

    def number(self, value: float) -> str:
        return format_number(value, self.language)

    # --- helpers --------------------------------------------------------

    def state_of(self, entity_id: str) -> State | None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        return state

    def float_state(self, entity_id: str) -> float | None:
        state = self.state_of(entity_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def friendly_name(self, entity_id: str, default: str | None = None) -> str:
        state = self.hass.states.get(entity_id)
        if state is not None:
            name = state.attributes.get("friendly_name")
            if name:
                return str(name)
        return default or entity_id.split(".", 1)[-1].replace("_", " ").title()
