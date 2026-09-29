"""Data model for predicted events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# Kept literal rather than imported from const so this module stays free of
# package-relative imports and can be unit tested on its own.
CONFIDENCE_CERTAIN = 1.0


@dataclass(slots=True)
class UpcomingEvent:
    """A single thing that is expected to happen in the near future."""

    key: str
    """Stable identifier, used to de-duplicate events across refreshes."""

    when: datetime
    """When the event is expected (timezone aware)."""

    title: str
    """Human readable one-liner, e.g. "Sonnenuntergang"."""

    kind: str
    """One of the KIND_* constants — used for grouping and card styling."""

    icon: str = "mdi:calendar-clock"
    confidence: float = CONFIDENCE_CERTAIN
    entity_id: str | None = None
    detail: str | None = None
    emoji: str = "•"
    extra: dict = field(default_factory=dict)

    @property
    def certain(self) -> bool:
        return self.confidence >= CONFIDENCE_CERTAIN

    def minutes_until(self, now: datetime) -> float:
        return (self.when - now).total_seconds() / 60

    def as_dict(self, now: datetime) -> dict:
        """Serialise for the state attributes and the Lovelace card."""
        return {
            "key": self.key,
            "when": self.when.isoformat(),
            "in_minutes": round(self.minutes_until(now), 1),
            "title": self.title,
            "kind": self.kind,
            "icon": self.icon,
            "emoji": self.emoji,
            "confidence": round(self.confidence, 2),
            "certain": self.certain,
            "entity_id": self.entity_id,
            "detail": self.detail,
            **self.extra,
        }
