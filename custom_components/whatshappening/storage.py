"""Keeping a provider's observations across a restart.

Most of what the providers know can be looked up again after a restart —
the sun, a timer, a calendar. What cannot is what they worked out by
watching: that the washing machine started its cycle at 18:05. Restarting
Home Assistant mid-cycle would otherwise reset that observation and the
estimate would start over from the restart.

Only providers that set `persist` are written out, and only values the JSON
store can hold: datetimes are wrapped on the way out and unwrapped on the
way back in.
"""

from __future__ import annotations

import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .serialize import decode, encode

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.memory"

# Written at most this often, so a 30 second refresh does not mean a disk
# write every 30 seconds. The throttling has to happen here rather than via
# the store's own delay: that delay restarts on every call, so a delay
# longer than the refresh interval would never elapse at all.
SAVE_INTERVAL = 300


class MemoryStore:
    """Loads and saves the parts of the provider memory worth keeping."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        # Start the clock now, so a restart does not write straight away.
        self._written_at = time.monotonic()

    async def async_load(self) -> dict:
        try:
            stored = await self._store.async_load()
        except Exception:  # noqa: BLE001 - a corrupt store must not block setup
            _LOGGER.warning("Could not read %s, starting fresh", STORAGE_KEY)
            return {}
        if not isinstance(stored, dict):
            return {}
        return decode(stored)

    def async_schedule_save(self, memory: dict) -> None:
        """Queue a write, unless one was queued recently."""
        if time.monotonic() - self._written_at < SAVE_INTERVAL:
            return
        self._written_at = time.monotonic()
        self._store.async_delay_save(lambda: encode(memory))

    async def async_save(self, memory: dict) -> None:
        """Write now — used when the entry is unloaded."""
        self._written_at = time.monotonic()
        await self._store.async_save(encode(memory))

    async def async_remove(self) -> None:
        await self._store.async_remove()
