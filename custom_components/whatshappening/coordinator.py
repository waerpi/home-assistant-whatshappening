"""Builds the timeline by asking every provider what it expects to happen."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HORIZON,
    DEFAULT_HORIZON,
    DEFAULTS,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .models import UpcomingEvent
from .providers import PROVIDERS, EventProvider
from .storage import MemoryStore

_LOGGER = logging.getLogger(__name__)


class WhatsHappeningCoordinator(DataUpdateCoordinator[list[UpcomingEvent]]):
    """Keeps an ordered list of the events expected within the horizon."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self._memory: dict = {}
        self._store = MemoryStore(hass)
        self._providers: list[EventProvider] = []
        self.reload_providers()

    # --- persistence ----------------------------------------------------

    async def async_load_memory(self) -> None:
        """Read the observations of the last run back in, before refreshing."""
        stored = await self._store.async_load()
        if not stored:
            return
        self._memory.update(stored)
        # The providers were built around the empty dict, so hand them the
        # namespaces that have just appeared in it.
        self.reload_providers()

    async def async_save_memory(self) -> None:
        await self._store.async_save(self._persistable())

    def _persistable(self) -> dict:
        """The provider namespaces that asked to be kept."""
        return {
            provider.name: self._memory.get(provider.name, {})
            for provider in self._providers
            if provider.persist
        }

    # --- configuration --------------------------------------------------

    @property
    def options(self) -> dict:
        return {**DEFAULTS, **self.entry.options}

    @property
    def horizon(self) -> timedelta:
        return timedelta(minutes=int(self.options.get(CONF_HORIZON, DEFAULT_HORIZON)))

    def reload_providers(self) -> None:
        """Rebuild the provider list after an options change.

        The memory dict is deliberately kept: observations such as appliance
        runtimes and sensor trends stay valid across a reconfiguration.
        """
        options = self.options
        self._providers = [
            provider(self.hass, options, self._memory) for provider in PROVIDERS
        ]

    # --- refresh --------------------------------------------------------

    async def _async_update_data(self) -> list[UpcomingEvent]:
        now = dt_util.now()
        horizon_end = now + self.horizon

        results = await asyncio.gather(
            *(
                provider.async_collect(now, horizon_end)
                for provider in self._providers
            )
        )
        self._store.async_schedule_save(self._persistable())
        return _merge([event for events in results for event in events])


def _merge(events: list[UpcomingEvent]) -> list[UpcomingEvent]:
    """Drop duplicates (keeping the soonest) and order by time."""
    unique: dict[str, UpcomingEvent] = {}
    for event in events:
        existing = unique.get(event.key)
        if existing is None or event.when < existing.when:
            unique[event.key] = event
    return sorted(unique.values(), key=lambda event: (event.when, event.title))
