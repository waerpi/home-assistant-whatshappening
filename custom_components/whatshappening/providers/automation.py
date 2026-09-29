"""Automations that are going to fire on a time or sun trigger."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from homeassistant.util import dt as dt_util

from ..const import CONF_ENABLE_AUTOMATIONS, CONFIDENCE_LIKELY, KIND_AUTOMATION
from ..models import UpcomingEvent
from ..predict import parse_offset
from .base import EventProvider

_LOGGER = logging.getLogger(__name__)

# HA renamed `platform:` to `trigger:` inside triggers in 2024.10; both
# spellings stay valid, so look at either.
PLATFORM_KEYS = ("platform", "trigger")

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")

SUN_ATTRIBUTE = {"sunrise": "next_rising", "sunset": "next_setting"}


class AutomationProvider(EventProvider):
    """Looks into automation configs for scheduled triggers.

    Only `time` and `sun` triggers can be predicted — state or event driven
    automations are, by definition, not on a timetable.
    """

    name = "automation"

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLE_AUTOMATIONS, True))

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for entity_id, config in self._automation_configs().items():
            state = self.hass.states.get(entity_id)
            if state is None or state.state != "on":
                continue  # a disabled automation will not fire

            triggers = config.get("triggers") or config.get("trigger") or []
            if isinstance(triggers, dict):
                triggers = [triggers]
            conditional = bool(config.get("conditions") or config.get("condition"))

            for index, trigger in enumerate(triggers):
                if not isinstance(trigger, dict):
                    continue
                for when in self._trigger_times(trigger, now):
                    if not now <= when <= horizon_end:
                        continue
                    events.append(
                        UpcomingEvent(
                            key=f"automation:{entity_id}:{index}",
                            when=when,
                            title=self.friendly_name(entity_id),
                            kind=KIND_AUTOMATION,
                            icon=state.attributes.get("icon") or "mdi:robot",
                            emoji="💡",
                            entity_id=entity_id,
                            detail=self.tr("automation.detail"),
                            # Conditions inside the automation may still veto it.
                            confidence=CONFIDENCE_LIKELY if conditional else 1.0,
                        )
                    )
        return events

    # --- config access --------------------------------------------------

    def _automation_configs(self) -> dict[str, dict]:
        """Raw configs of all loaded automations, keyed by entity id.

        This reaches into the automation component's entity objects because
        there is no public API for it; a failure here simply means no
        automation events.
        """
        component = self.hass.data.get("entity_components", {}).get("automation")
        if component is None:
            return {}

        configs: dict[str, dict] = {}
        for entity in component.entities:
            raw_config = getattr(entity, "raw_config", None)
            if isinstance(raw_config, dict):
                configs[entity.entity_id] = raw_config
        return configs

    # --- trigger evaluation ---------------------------------------------

    def _trigger_times(self, trigger: dict, now: datetime) -> list[datetime]:
        platform = next((trigger[key] for key in PLATFORM_KEYS if key in trigger), None)
        if platform == "time":
            return self._time_trigger(trigger, now)
        if platform == "sun":
            return self._sun_trigger(trigger)
        return []

    def _time_trigger(self, trigger: dict, now: datetime) -> list[datetime]:
        values = trigger.get("at")
        if values is None:
            return []
        if not isinstance(values, list):
            values = [values]

        times: list[datetime] = []
        for value in values:
            if isinstance(value, dict):  # {"entity_id": ..., "offset": ...}
                offset = parse_offset(value.get("offset"))
                value = value.get("entity_id")
            else:
                offset = timedelta()
            if not isinstance(value, str):
                continue
            when = self._parse_clock_time(value, now) or self._entity_time(value, now)
            if when is not None:
                times.append(when + offset)
        return times

    def _sun_trigger(self, trigger: dict) -> list[datetime]:
        attribute = SUN_ATTRIBUTE.get(str(trigger.get("event")))
        if attribute is None:
            return []
        sun = self.state_of("sun.sun")
        if sun is None:
            return []
        raw = sun.attributes.get(attribute)
        if not raw:
            return []
        when = dt_util.parse_datetime(str(raw))
        if when is None:
            return []
        return [dt_util.as_local(when) + parse_offset(trigger.get("offset"))]

    @staticmethod
    def _parse_clock_time(value: str, now: datetime) -> datetime | None:
        match = TIME_RE.match(value.strip())
        if match is None:
            return None
        hour, minute, second = (int(part or 0) for part in match.groups())
        candidate = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        if candidate < now:
            candidate += timedelta(days=1)
        return candidate

    def _entity_time(self, entity_id: str, now: datetime) -> datetime | None:
        """A time trigger may point at an input_datetime or timestamp sensor."""
        if "." not in entity_id:
            return None
        state = self.state_of(entity_id)
        if state is None:
            return None

        timestamp = state.attributes.get("timestamp")
        if timestamp is not None:
            if state.attributes.get("has_date", True):
                return dt_util.as_local(dt_util.utc_from_timestamp(float(timestamp)))
            candidate = dt_util.start_of_local_day(now) + timedelta(
                seconds=float(timestamp)
            )
            return candidate if candidate >= now else candidate + timedelta(days=1)

        parsed = dt_util.parse_datetime(state.state)
        return dt_util.as_local(parsed) if parsed else None
