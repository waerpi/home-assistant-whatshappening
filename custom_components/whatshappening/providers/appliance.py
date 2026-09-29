"""Appliances that are mid-cycle: when are they going to be done?

Two sources, in order of trust:

1. a "remaining time" sensor the appliance itself publishes — that is the
   appliance's own estimate and we simply pass it through;
2. otherwise the power draw: once the appliance has been above its idle
   threshold for a while we know when the cycle started, and a typical
   cycle length tells us roughly when it ends.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.util import dt as dt_util

from ..const import (
    CONF_APPLIANCE_CYCLE,
    CONF_APPLIANCE_MIN_RUNTIME,
    CONF_APPLIANCE_THRESHOLD,
    CONF_APPLIANCES,
    CONF_REMAINING_SENSORS,
    CONFIDENCE_GUESS,
    CONFIDENCE_LIKELY,
    DEFAULT_APPLIANCE_CYCLE,
    DEFAULT_APPLIANCE_MIN_RUNTIME,
    DEFAULT_APPLIANCE_THRESHOLD,
    KIND_APPLIANCE,
)
from ..models import UpcomingEvent
from .base import EventProvider

# Short dips below the threshold are normal mid-cycle (a washing machine
# idles between heating and spinning), so only a sustained drop ends a run.
IDLE_GRACE = timedelta(minutes=5)

# Suffixes stripped from a power sensor's object id to find the appliance.
POWER_SUFFIXES = (
    "_power",
    "_current_power",
    "_power_consumption",
    "_active_power",
    "_energy_power",
    "_watt",
)


class ApplianceProvider(EventProvider):
    """Predicts when a running appliance finishes."""

    name = "appliance"

    @property
    def entities(self) -> list[str]:
        return list(self.options.get(CONF_APPLIANCES) or [])

    @property
    def enabled(self) -> bool:
        return bool(self.entities)

    @property
    def threshold(self) -> float:
        return float(
            self.options.get(CONF_APPLIANCE_THRESHOLD, DEFAULT_APPLIANCE_THRESHOLD)
        )

    @property
    def cycle(self) -> timedelta:
        minutes = self.options.get(CONF_APPLIANCE_CYCLE, DEFAULT_APPLIANCE_CYCLE)
        return timedelta(minutes=float(minutes))

    @property
    def min_runtime(self) -> timedelta:
        return timedelta(
            minutes=float(
                self.options.get(
                    CONF_APPLIANCE_MIN_RUNTIME, DEFAULT_APPLIANCE_MIN_RUNTIME
                )
            )
        )

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for entity_id in self.entities:
            run = self._track(entity_id, now)
            if run is None:
                continue

            name = self._appliance_name(entity_id)
            remaining = self._remaining_for(entity_id, now)
            if remaining is not None:
                events.append(
                    UpcomingEvent(
                        key=f"appliance:{entity_id}",
                        when=remaining,
                        title=f"{name} fertig",
                        kind=KIND_APPLIANCE,
                        icon="mdi:washing-machine",
                        emoji="🔌",
                        entity_id=entity_id,
                        detail="laut Restlaufzeit",
                        confidence=CONFIDENCE_LIKELY,
                    )
                )
                continue

            if now - run["started_at"] < self.min_runtime:
                continue  # too early to tell a cycle from a short burst
            events.append(
                UpcomingEvent(
                    key=f"appliance:{entity_id}",
                    when=run["started_at"] + self.cycle,
                    title=f"{name} vermutlich fertig",
                    kind=KIND_APPLIANCE,
                    icon="mdi:washing-machine",
                    emoji="🔌",
                    entity_id=entity_id,
                    detail="geschätzt aus der Laufzeit",
                    confidence=CONFIDENCE_GUESS,
                )
            )
        return events

    # --- run tracking ---------------------------------------------------

    def _track(self, entity_id: str, now: datetime) -> dict | None:
        """Update and return the current run for an appliance, if any."""
        power = self.float_state(entity_id)
        run = self.memory.get(entity_id)

        if power is not None and power >= self.threshold:
            if run is None:
                run = {"started_at": now}
                self.memory[entity_id] = run
            run["last_active"] = now
            return run

        if run is None:
            return None
        if now - run["last_active"] <= IDLE_GRACE:
            return run  # a pause inside the cycle, not the end of it

        del self.memory[entity_id]
        return None

    # --- remaining time sensors -----------------------------------------

    def _remaining_for(self, power_entity: str, now: datetime) -> datetime | None:
        """Find the appliance's own remaining-time sensor, if configured."""
        prefix = self._appliance_slug(power_entity)
        for entity_id in self.options.get(CONF_REMAINING_SENSORS) or []:
            if not entity_id.split(".", 1)[-1].startswith(prefix):
                continue
            state = self.state_of(entity_id)
            if state is None:
                continue

            if state.attributes.get("device_class") == "timestamp":
                when = dt_util.parse_datetime(state.state)
                if when is not None:
                    return dt_util.as_local(when)
                continue

            minutes = self.float_state(entity_id)
            if minutes is None or minutes <= 0:
                continue
            unit = str(state.attributes.get("unit_of_measurement") or "min").lower()
            if unit in ("s", "sec", "seconds"):
                return now + timedelta(seconds=minutes)
            if unit in ("h", "hour", "hours"):
                return now + timedelta(hours=minutes)
            return now + timedelta(minutes=minutes)
        return None

    # --- naming ---------------------------------------------------------

    @staticmethod
    def _appliance_slug(power_entity: str) -> str:
        object_id = power_entity.split(".", 1)[-1]
        for suffix in POWER_SUFFIXES:
            if object_id.endswith(suffix):
                return object_id[: -len(suffix)]
        return object_id

    def _appliance_name(self, power_entity: str) -> str:
        name = self.friendly_name(power_entity)
        for suffix in (" Power", " Leistung", " Verbrauch", " Stromverbrauch"):
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name
