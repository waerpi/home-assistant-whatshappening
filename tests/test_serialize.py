"""Tests for the memory's JSON round trip."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from conftest import load

serialize = load("serialize")

BERLIN = timezone(timedelta(hours=2))
STARTED = datetime(2026, 9, 29, 18, 5, tzinfo=BERLIN)


def roundtrip(value):
    return serialize.decode(serialize.encode(value))


class TestRoundTrip:
    def test_a_tracked_appliance_run_survives(self):
        memory = {
            "appliance": {
                "sensor.washing_machine_power": {
                    "started_at": STARTED,
                    "last_active": STARTED + timedelta(minutes=12),
                }
            }
        }
        assert roundtrip(memory) == memory

    def test_the_timezone_is_kept(self):
        restored = roundtrip({"started_at": STARTED})["started_at"]
        assert restored.tzinfo is not None
        assert restored == STARTED

    @pytest.mark.parametrize(
        "value",
        [{}, {"a": 1}, {"a": 1.5}, {"a": "text"}, {"a": True}, {"a": None}, [1, 2]],
    )
    def test_plain_values_pass_through(self, value):
        assert roundtrip(value) == value

    def test_nested_structures_are_walked(self):
        value = {"a": [{"when": STARTED}, {"when": STARTED}]}
        assert roundtrip(value) == value

    def test_tuples_become_lists(self):
        # JSON has no tuples; the sample buffers index into these, so a list
        # is just as good as long as the order is kept.
        assert roundtrip({"samples": [(1.0, 20.0), (2.0, 21.0)]}) == {
            "samples": [[1.0, 20.0], [2.0, 21.0]]
        }


class TestEncode:
    def test_a_datetime_becomes_a_marked_string(self):
        assert serialize.encode(STARTED) == {
            serialize.DT_MARKER: "2026-09-29T18:05:00+02:00"
        }

    def test_keys_become_strings(self):
        assert serialize.encode({1: "x"}) == {"1": "x"}


class TestDecode:
    def test_an_unreadable_marker_becomes_none(self):
        assert serialize.decode({serialize.DT_MARKER: "not a date"}) is None

    def test_a_naive_datetime_is_refused(self):
        # Nothing `encode` writes is naive, and a naive value cannot be
        # compared against "now" without guessing a timezone.
        assert serialize.decode({serialize.DT_MARKER: "2026-09-29T18:05:00"}) is None

    def test_a_dict_that_only_looks_like_a_marker_is_left_alone(self):
        value = {serialize.DT_MARKER: "2026-09-29T18:05:00+02:00", "other": 1}
        assert serialize.decode(value) == value

    def test_unknown_input_is_returned_unchanged(self):
        assert serialize.decode("plain") == "plain"
