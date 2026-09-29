"""Sensors exposing the timeline."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_HORIZON, DEFAULT_HORIZON, DOMAIN
from .coordinator import WhatsHappeningCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WhatsHappeningCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            UpcomingEventsSensor(coordinator, entry),
            NextEventSensor(coordinator, entry),
        ]
    )


class WhatsHappeningEntity(CoordinatorEntity[WhatsHappeningCoordinator], SensorEntity):
    """Shared device info and coordinator plumbing."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: WhatsHappeningCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Was passiert gleich?",
            manufacturer="whatshappening",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _events(self):
        return self.coordinator.data or []


class UpcomingEventsSensor(WhatsHappeningEntity):
    """How many events are expected, with the full timeline in attributes."""

    # Named after the device, so it becomes `sensor.was_passiert_gleich`.
    _attr_name = None
    _attr_icon = "mdi:timeline-clock-outline"
    _attr_native_unit_of_measurement = "Ereignisse"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_upcoming"

    @property
    def native_value(self) -> int:
        return len(self._events)

    @property
    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        horizon = int(self.coordinator.options.get(CONF_HORIZON, DEFAULT_HORIZON))
        return {
            "horizon_minutes": horizon,
            "generated_at": now.isoformat(),
            "events": [event.as_dict(now) for event in self._events],
        }


class NextEventSensor(WhatsHappeningEntity):
    """The single next thing that is going to happen."""

    _attr_name = "Nächstes Ereignis"
    _attr_icon = "mdi:progress-clock"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next"

    @property
    def native_value(self) -> str | None:
        events = self._events
        if not events:
            return None
        # State strings are capped at 255 characters by the state machine.
        return events[0].title[:255]

    @property
    def extra_state_attributes(self) -> dict:
        events = self._events
        if not events:
            return {}
        return events[0].as_dict(dt_util.now())
