"""Event providers — every source the timeline is built from."""

from __future__ import annotations

from .appliance import ApplianceProvider
from .automation import AutomationProvider
from .base import EventProvider
from .calendar import CalendarProvider
from .helpers import InputDatetimeProvider, ScheduleProvider, TimerProvider
from .presence import PresenceProvider
from .sun import SunProvider
from .trend import TrendProvider

PROVIDERS: tuple[type[EventProvider], ...] = (
    SunProvider,
    CalendarProvider,
    ScheduleProvider,
    TimerProvider,
    InputDatetimeProvider,
    AutomationProvider,
    PresenceProvider,
    ApplianceProvider,
    TrendProvider,
)

__all__ = ["PROVIDERS", "EventProvider"]
