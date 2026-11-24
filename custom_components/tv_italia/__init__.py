"""TV Italia: guida ai canali televisivi italiani per Home Assistant."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, CARD_VERSION, DOMAIN
from .coordinator import TvItaliaCoordinator
from .services import async_setup_services

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type TvItaliaConfigEntry = ConfigEntry[TvItaliaCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registra le azioni dell'integrazione."""
    async_setup_services(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve la card Lovelace e la carica automaticamente nel frontend."""
    if hass.data.get(f"{DOMAIN}_card_registered"):
        return
    card_path = Path(__file__).parent / "frontend" / "tv-italia-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_path), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
    hass.data[f"{DOMAIN}_card_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: TvItaliaConfigEntry) -> bool:
    """Configura l'integrazione da una config entry."""
    coordinator = TvItaliaCoordinator(hass, entry)
    await coordinator.async_load_favorites()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await _async_register_card(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: TvItaliaConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: TvItaliaConfigEntry) -> bool:
    """Rimuove l'integrazione."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
