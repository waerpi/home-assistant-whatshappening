"""Where a numeric sensor is heading.

Temperature, humidity or battery level rarely jump — they drift. Fitting a
line through the last few readings therefore gives a usable estimate of the
value at the end of the horizon, and the quality of that fit tells us how
much to trust it.
"""

from __future__ import annotations

from datetime import datetime

from ..const import (
    CONF_TREND_SENSORS,
    CONFIDENCE_GUESS,
    CONFIDENCE_LIKELY,
    KIND_TREND,
    TREND_MIN_DELTA,
    TREND_MIN_SAMPLES,
    TREND_WINDOW,
)
from ..models import UpcomingEvent
from ..predict import linear_fit
from .base import EventProvider

ICONS = {
    "temperature": "mdi:thermometer",
    "humidity": "mdi:water-percent",
    "battery": "mdi:battery",
    "power": "mdi:flash",
    "illuminance": "mdi:brightness-6",
    "carbon_dioxide": "mdi:molecule-co2",
}

EMOJIS = {
    "temperature": "🌡",
    "humidity": "💧",
    "battery": "🔋",
    "power": "⚡",
    "illuminance": "🔆",
}


class TrendProvider(EventProvider):
    """Extrapolates the configured numeric sensors to the end of the horizon."""

    name = "trend"

    @property
    def entities(self) -> list[str]:
        return list(self.options.get(CONF_TREND_SENSORS) or [])

    @property
    def enabled(self) -> bool:
        return bool(self.entities)

    async def async_get_events(
        self, now: datetime, horizon_end: datetime
    ) -> list[UpcomingEvent]:
        events: list[UpcomingEvent] = []
        for entity_id in self.entities:
            samples = self._record(entity_id, now)
            if len(samples) < TREND_MIN_SAMPLES:
                continue

            fit = linear_fit(samples)
            if fit is None:
                continue
            slope, intercept, quality = fit

            horizon_seconds = horizon_end.timestamp()
            predicted = slope * horizon_seconds + intercept
            current = samples[-1][1]
            if abs(predicted - current) < TREND_MIN_DELTA:
                continue  # not moving enough to be worth a line on the card

            state = self.hass.states.get(entity_id)
            attributes = state.attributes if state else {}
            device_class = str(attributes.get("device_class") or "")
            unit = str(attributes.get("unit_of_measurement") or "").strip()
            name = self.friendly_name(entity_id)

            events.append(
                UpcomingEvent(
                    key=f"trend:{entity_id}",
                    when=horizon_end,
                    title=self.tr(
                        "trend.prediction",
                        name=name,
                        value=self._with_unit(predicted, unit),
                    ),
                    kind=KIND_TREND,
                    icon=ICONS.get(device_class, "mdi:chart-line"),
                    emoji=EMOJIS.get(device_class, "📈"),
                    entity_id=entity_id,
                    detail=self.tr(
                        "trend.detail_current",
                        value=self._with_unit(current, unit),
                    ),
                    confidence=(
                        CONFIDENCE_LIKELY if quality >= 0.8 else CONFIDENCE_GUESS
                    ),
                    extra={
                        "predicted": round(predicted, 2),
                        "current": round(current, 2),
                        "unit": unit,
                    },
                )
            )
        return events

    def _with_unit(self, value: float, unit: str) -> str:
        return f"{self.number(value)} {unit}".strip()

    def _record(self, entity_id: str, now: datetime) -> list[tuple[float, float]]:
        """Append the current reading and drop everything past the window."""
        value = self.float_state(entity_id)
        samples: list[tuple[float, float]] = self.memory.setdefault(entity_id, [])
        if value is not None:
            samples.append((now.timestamp(), value))

        cutoff = now.timestamp() - TREND_WINDOW.total_seconds()
        samples[:] = [sample for sample in samples if sample[0] >= cutoff]
        return samples


