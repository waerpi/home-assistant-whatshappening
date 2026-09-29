"""Constants for the "Was passiert gleich?" integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "whatshappening"

PLATFORMS = ["sensor"]

UPDATE_INTERVAL = timedelta(seconds=30)

# --- configuration keys -------------------------------------------------

CONF_HORIZON = "horizon_minutes"
CONF_CALENDARS = "calendars"
CONF_TREND_SENSORS = "trend_sensors"
CONF_TRAVEL_SENSORS = "travel_sensors"
CONF_APPLIANCES = "appliances"
CONF_APPLIANCE_THRESHOLD = "appliance_threshold"
CONF_APPLIANCE_CYCLE = "appliance_cycle_minutes"
CONF_APPLIANCE_MIN_RUNTIME = "appliance_min_runtime_minutes"
CONF_REMAINING_SENSORS = "remaining_sensors"
CONF_ENABLE_SUN = "enable_sun"
CONF_ENABLE_SCHEDULES = "enable_schedules"
CONF_ENABLE_TIMERS = "enable_timers"
CONF_ENABLE_AUTOMATIONS = "enable_automations"
CONF_ENABLE_INPUT_DATETIME = "enable_input_datetime"

DEFAULT_HORIZON = 30
DEFAULT_APPLIANCE_THRESHOLD = 5.0
DEFAULT_APPLIANCE_CYCLE = 120
DEFAULT_APPLIANCE_MIN_RUNTIME = 3

DEFAULTS: dict = {
    CONF_HORIZON: DEFAULT_HORIZON,
    CONF_CALENDARS: [],
    CONF_TREND_SENSORS: [],
    CONF_TRAVEL_SENSORS: [],
    CONF_APPLIANCES: [],
    CONF_REMAINING_SENSORS: [],
    CONF_APPLIANCE_THRESHOLD: DEFAULT_APPLIANCE_THRESHOLD,
    CONF_APPLIANCE_CYCLE: DEFAULT_APPLIANCE_CYCLE,
    CONF_APPLIANCE_MIN_RUNTIME: DEFAULT_APPLIANCE_MIN_RUNTIME,
    CONF_ENABLE_SUN: True,
    CONF_ENABLE_SCHEDULES: True,
    CONF_ENABLE_TIMERS: True,
    CONF_ENABLE_AUTOMATIONS: True,
    CONF_ENABLE_INPUT_DATETIME: True,
}

# --- event kinds --------------------------------------------------------

KIND_SUN = "sun"
KIND_CALENDAR = "calendar"
KIND_SCHEDULE = "schedule"
KIND_TIMER = "timer"
KIND_DATETIME = "datetime"
KIND_AUTOMATION = "automation"
KIND_PRESENCE = "presence"
KIND_APPLIANCE = "appliance"
KIND_TREND = "trend"

# How certain a prediction is. Anything below 1.0 is phrased as a guess
# ("likely", "expected") and rendered in italics by the card.
CONFIDENCE_CERTAIN = 1.0
CONFIDENCE_LIKELY = 0.7
CONFIDENCE_GUESS = 0.4

# Trend detection: how long a history we keep per sensor and how much a
# value has to move before it is worth mentioning.
TREND_WINDOW = timedelta(minutes=45)
TREND_MIN_SAMPLES = 4
TREND_MIN_DELTA = 0.3
