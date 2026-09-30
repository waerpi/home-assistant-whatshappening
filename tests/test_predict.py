"""Tests for the prediction maths."""

from __future__ import annotations

from datetime import timedelta

import pytest
from conftest import load

predict = load("predict")


class TestLinearFit:
    def test_perfect_line_is_recovered(self):
        samples = [(0.0, 20.0), (60.0, 21.0), (120.0, 22.0), (180.0, 23.0)]
        slope, intercept, quality = predict.linear_fit(samples)

        assert slope == pytest.approx(1 / 60)
        assert intercept == pytest.approx(20.0)
        assert quality == pytest.approx(1.0)

    def test_extrapolates_a_rising_temperature(self):
        # 20.0 °C rising by 1 °C every 10 minutes, sampled every 5 minutes.
        samples = [(minute * 60.0, 20.0 + minute / 10) for minute in range(0, 25, 5)]
        slope, intercept, _ = predict.linear_fit(samples)

        at_30_minutes = slope * 30 * 60 + intercept
        assert at_30_minutes == pytest.approx(23.0)

    def test_noise_lowers_the_quality(self):
        noisy = [(0.0, 20.0), (60.0, 24.0), (120.0, 20.5), (180.0, 23.0)]
        _, _, quality = predict.linear_fit(noisy)
        assert quality < 0.5

    def test_flat_series_is_a_perfect_fit_with_zero_slope(self):
        slope, _, quality = predict.linear_fit(
            [(0.0, 21.0), (60.0, 21.0), (120.0, 21.0)]
        )
        assert slope == 0.0
        assert quality == 1.0

    @pytest.mark.parametrize(
        "samples",
        [[], [(0.0, 20.0)], [(5.0, 20.0), (5.0, 21.0)]],
    )
    def test_returns_none_without_usable_samples(self, samples):
        assert predict.linear_fit(samples) is None


class TestParseOffset:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, timedelta()),
            ("00:15:00", timedelta(minutes=15)),
            ("-00:15:00", timedelta(minutes=-15)),
            ("+01:30:00", timedelta(hours=1, minutes=30)),
            ("00:15", timedelta(minutes=15)),
            (900, timedelta(seconds=900)),
            (-900.0, timedelta(seconds=-900)),
            ({"minutes": 15}, timedelta(minutes=15)),
            (timedelta(minutes=15), timedelta(minutes=15)),
        ],
    )
    def test_supported_spellings(self, value, expected):
        assert predict.parse_offset(value) == expected

    @pytest.mark.parametrize("value", ["soon", "", {"nonsense": "x"}, True])
    def test_unparseable_offsets_are_ignored(self, value):
        assert predict.parse_offset(value) == timedelta()


class TestMinutesFrom:
    @pytest.mark.parametrize(
        ("value", "unit", "expected"),
        [
            (12, "min", 12),
            (12, "minutes", 12),
            (12, "Minuten", 12),
            (90, "s", 1.5),
            (90, "seconds", 1.5),
            (2, "h", 120),
            (2, "Stunden", 120),
            (1.5, "hrs.", 90),
        ],
    )
    def test_converts_to_minutes(self, value, unit, expected):
        assert predict.minutes_from(value, unit) == pytest.approx(expected)

    @pytest.mark.parametrize("unit", [None, "", "  ", "km", "unknown"])
    def test_falls_back_to_minutes(self, unit):
        # A travel time sensor without a usable unit is almost always
        # reporting minutes, so that is the safer reading.
        assert predict.minutes_from(12, unit) == 12

    def test_no_reading_stays_no_reading(self):
        assert predict.minutes_from(None, "min") is None


class TestMergeSamples:
    def test_orders_and_combines_both_series(self):
        merged = predict.merge_samples([(30.0, 2.0)], [(10.0, 1.0), (20.0, 1.5)])
        assert merged == [(10.0, 1.0), (20.0, 1.5), (30.0, 2.0)]

    def test_primary_wins_on_a_shared_timestamp(self):
        # The live reading is the one that was actually observed now; the
        # recorder's copy of the same moment must not overwrite it.
        merged = predict.merge_samples([(10.0, 9.0)], [(10.0, 1.0)])
        assert merged == [(10.0, 9.0)]

    def test_drops_samples_before_the_cutoff(self):
        merged = predict.merge_samples(
            [(30.0, 2.0)], [(5.0, 0.5), (10.0, 1.0)], cutoff=10.0
        )
        assert merged == [(10.0, 1.0), (30.0, 2.0)]

    def test_empty_series_are_fine(self):
        assert predict.merge_samples([], []) == []

    def test_result_feeds_straight_into_a_fit(self):
        merged = predict.merge_samples(
            [(180.0, 23.0)], [(0.0, 20.0), (60.0, 21.0), (120.0, 22.0)]
        )
        slope, _, quality = predict.linear_fit(merged)
        assert slope == pytest.approx(1 / 60)
        assert quality == pytest.approx(1.0)
