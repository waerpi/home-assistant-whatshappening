"""Turning a provider's memory into JSON and back.

The memory holds datetimes, which JSON does not, so they travel wrapped in
a one-key marker dict. Deliberately free of Home Assistant imports, which
keeps it unit testable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Chosen so it cannot collide with a key a provider would use itself.
DT_MARKER = "__datetime__"


def encode(value: Any) -> Any:
    """Turn a memory tree into something the JSON store can hold."""
    if isinstance(value, datetime):
        return {DT_MARKER: value.isoformat()}
    if isinstance(value, dict):
        return {str(key): encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [encode(item) for item in value]
    return value


def decode(value: Any) -> Any:
    """Reverse `encode`.

    A marker that no longer parses becomes None rather than raising: a
    memory is an optimisation, and a single unreadable value in it must not
    cost the whole store.
    """
    if isinstance(value, dict):
        if set(value) == {DT_MARKER}:
            return _parse(value[DT_MARKER])
        return {key: decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decode(item) for item in value]
    return value


def _parse(raw: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None
    # Everything written out is timezone aware; anything that is not did not
    # come from `encode` and cannot be compared against "now".
    return parsed if parsed.tzinfo is not None else None
