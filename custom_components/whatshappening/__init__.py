"""The "Was passiert gleich?" integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import WhatsHappeningCoordinator

_LOGGER = logging.getLogger(__name__)

CARD_URL = f"/{DOMAIN}/whatshappening-card.js"
CARD_FILE = "frontend/whatshappening-card.js"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_card(hass)

    coordinator = WhatsHappeningCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator: WhatsHappeningCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.reload_providers()
    await coordinator.async_request_refresh()


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the Lovelace card and load it, so no manual resource is needed."""
    if hass.data.get(f"{DOMAIN}_card_registered"):
        return

    path = str(Path(__file__).parent / CARD_FILE)
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, path, cache_headers=False)]
        )
    except ImportError:  # Home Assistant < 2024.7
        hass.http.register_static_path(CARD_URL, path, cache_headers=False)

    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
    except Exception:  # noqa: BLE001 - the card can still be added by hand
        _LOGGER.warning(
            "Could not auto-load the Lovelace card; add %s as a dashboard "
            "resource manually",
            CARD_URL,
        )

    hass.data[f"{DOMAIN}_card_registered"] = True
