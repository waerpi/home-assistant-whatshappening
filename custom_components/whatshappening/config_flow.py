"""Config and options flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_APPLIANCE_CYCLE,
    CONF_APPLIANCE_MIN_RUNTIME,
    CONF_APPLIANCE_THRESHOLD,
    CONF_APPLIANCES,
    CONF_CALENDARS,
    CONF_ENABLE_AUTOMATIONS,
    CONF_ENABLE_INPUT_DATETIME,
    CONF_ENABLE_SCHEDULES,
    CONF_ENABLE_SUN,
    CONF_ENABLE_TIMERS,
    CONF_HORIZON,
    CONF_REMAINING_SENSORS,
    CONF_TRAVEL_SENSORS,
    CONF_TREND_SENSORS,
    DEFAULTS,
    DOMAIN,
)

TITLE = "What's happening next?"


def _sensors(**kwargs: Any) -> EntitySelector:
    return EntitySelector(
        EntitySelectorConfig(domain="sensor", multiple=True, **kwargs)
    )


def _number(minimum: float, maximum: float, step: float, unit: str) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            unit_of_measurement=unit,
            mode=NumberSelectorMode.BOX,
        )
    )


def options_schema(options: dict) -> vol.Schema:
    """Build the options form, pre-filled with the current values."""
    current = {**DEFAULTS, **options}

    def default(key: str) -> Any:
        return current.get(key)

    return vol.Schema(
        {
            vol.Required(CONF_HORIZON, default=default(CONF_HORIZON)): _number(
                5, 720, 5, "min"
            ),
            vol.Optional(CONF_CALENDARS, default=default(CONF_CALENDARS)): (
                EntitySelector(EntitySelectorConfig(domain="calendar", multiple=True))
            ),
            vol.Optional(
                CONF_TREND_SENSORS, default=default(CONF_TREND_SENSORS)
            ): _sensors(),
            vol.Optional(
                CONF_TRAVEL_SENSORS, default=default(CONF_TRAVEL_SENSORS)
            ): _sensors(),
            vol.Optional(CONF_APPLIANCES, default=default(CONF_APPLIANCES)): _sensors(
                device_class="power"
            ),
            vol.Optional(
                CONF_REMAINING_SENSORS, default=default(CONF_REMAINING_SENSORS)
            ): _sensors(),
            vol.Required(
                CONF_APPLIANCE_THRESHOLD, default=default(CONF_APPLIANCE_THRESHOLD)
            ): _number(0.1, 5000, 0.1, "W"),
            vol.Required(
                CONF_APPLIANCE_CYCLE, default=default(CONF_APPLIANCE_CYCLE)
            ): _number(5, 600, 5, "min"),
            vol.Required(
                CONF_APPLIANCE_MIN_RUNTIME,
                default=default(CONF_APPLIANCE_MIN_RUNTIME),
            ): _number(0, 60, 1, "min"),
            vol.Required(
                CONF_ENABLE_SUN, default=default(CONF_ENABLE_SUN)
            ): BooleanSelector(),
            vol.Required(
                CONF_ENABLE_SCHEDULES, default=default(CONF_ENABLE_SCHEDULES)
            ): BooleanSelector(),
            vol.Required(
                CONF_ENABLE_TIMERS, default=default(CONF_ENABLE_TIMERS)
            ): BooleanSelector(),
            vol.Required(
                CONF_ENABLE_AUTOMATIONS, default=default(CONF_ENABLE_AUTOMATIONS)
            ): BooleanSelector(),
            vol.Required(
                CONF_ENABLE_INPUT_DATETIME, default=default(CONF_ENABLE_INPUT_DATETIME)
            ): BooleanSelector(),
        }
    )


class WhatsHappeningConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set the integration up — there is only ever one instance."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=TITLE, data={}, options=user_input)

        return self.async_show_form(
            step_id="user", data_schema=options_schema(dict(DEFAULTS))
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WhatsHappeningOptionsFlow(config_entry)


class WhatsHappeningOptionsFlow(OptionsFlow):
    """Reconfigure sources and the horizon."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init", data_schema=options_schema(dict(self._entry.options))
        )
