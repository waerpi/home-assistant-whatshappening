"""Tests for the event model."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conftest import load

models = load("models")

NOW = datetime(2026, 9, 29, 19, 30, tzinfo=UTC)


def make_event(**kwargs):
    defaults = {
        "key": "sun:next_setting",
        "when": NOW + timedelta(minutes=12),
        "title": "Sonnenuntergang",
        "kind": "sun",
    }
    return models.UpcomingEvent(**{**defaults, **kwargs})


def test_minutes_until():
    assert make_event().minutes_until(NOW) == 12.0


def test_events_default_to_certain():
    assert make_event().certain is True


def test_a_prediction_is_not_certain():
    assert make_event(confidence=0.4).certain is False


def test_as_dict_is_serialisable_for_the_card():
    event = make_event(
        emoji="🌅",
        icon="mdi:weather-sunset-down",
        entity_id="sun.sun",
        detail="heute",
    )
    payload = event.as_dict(NOW)

    assert payload == {
        "key": "sun:next_setting",
        "when": "2026-09-29T19:42:00+00:00",
        "in_minutes": 12.0,
        "title": "Sonnenuntergang",
        "kind": "sun",
        "icon": "mdi:weather-sunset-down",
        "emoji": "🌅",
        "confidence": 1.0,
        "certain": True,
        "entity_id": "sun.sun",
        "detail": "heute",
    }


def test_extra_fields_are_merged_into_the_payload():
    payload = make_event(extra={"predicted": 21.8, "unit": "°C"}).as_dict(NOW)
    assert payload["predicted"] == 21.8
    assert payload["unit"] == "°C"
