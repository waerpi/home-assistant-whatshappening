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

    @pytest.mark.parametrize("value", ["bald", "", {"nonsense": "x"}, True])
    def test_unparseable_offsets_are_ignored(self, value):
        assert predict.parse_offset(value) == timedelta()


class TestFormatNumber:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(21.84, "21,8"), (21.0, "21,0"), (-3.27, "-3,3"), (100.0, "100,0")],
    )
    def test_german_decimal_separator(self, value, expected):
        assert predict.format_number(value) == expected
