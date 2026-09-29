"""Pure prediction maths, deliberately free of Home Assistant imports."""

from __future__ import annotations

import re
from datetime import timedelta

OFFSET_RE = re.compile(r"^(?P<sign>[-+])?(\d{1,3}):(\d{2})(?::(\d{2}))?$")


def linear_fit(
    samples: list[tuple[float, float]],
) -> tuple[float, float, float] | None:
    """Least-squares fit through (x, y) samples, as (slope, intercept, r²).

    Returns None when the samples share a single x value, which carries no
    information about a trend.
    """
    count = len(samples)
    if count < 2:
        return None

    mean_x = sum(x for x, _ in samples) / count
    mean_y = sum(y for _, y in samples) / count

    variance_x = sum((x - mean_x) ** 2 for x, _ in samples)
    if variance_x == 0:
        return None
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in samples)

    slope = covariance / variance_x
    intercept = mean_y - slope * mean_x

    variance_y = sum((y - mean_y) ** 2 for _, y in samples)
    if variance_y == 0:
        return slope, intercept, 1.0
    residuals = sum((y - (slope * x + intercept)) ** 2 for x, y in samples)
    return slope, intercept, max(0.0, 1 - residuals / variance_y)


def parse_offset(value) -> timedelta:
    """Accept `"-00:15:00"`, `900` or `{"minutes": 15}` style offsets."""
    if value is None:
        return timedelta()
    if isinstance(value, timedelta):
        return value
    if isinstance(value, bool):
        return timedelta()
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    if isinstance(value, dict):
        try:
            return timedelta(**{key: float(val) for key, val in value.items()})
        except (TypeError, ValueError):
            return timedelta()

    match = OFFSET_RE.match(str(value).strip())
    if match is None:
        return timedelta()
    sign = -1 if match.group("sign") == "-" else 1
    hours, minutes, seconds = (int(part or 0) for part in match.groups()[1:])
    return sign * timedelta(hours=hours, minutes=minutes, seconds=seconds)


def format_number(value: float) -> str:
    """German formatting: one decimal, comma as the separator."""
    return f"{value:.1f}".replace(".", ",")
