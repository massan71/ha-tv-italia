"""Azioni di TV Italia: preferiti e riepilogo della prima serata."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import CHANNELS_BY_KEY, DOMAIN
from .coordinator import TvItaliaCoordinator, prime_time_programme
from .epg import genre_of

SERVICE_SET_FAVORITE = "set_favorite"
SERVICE_STASERA = "stasera"

ATTR_FAVORITE = "favorite"
ATTR_ONLY_FAVORITES = "only_favorites"
ATTR_PLATFORM = "platform"

SET_FAVORITE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_FAVORITE): cv.boolean,
    }
)
STASERA_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ONLY_FAVORITES, default=False): cv.boolean,
        vol.Optional(ATTR_PLATFORM, default="all"): vol.In(["all", "dtt", "sky"]),
    }
)


def _coordinator(hass: HomeAssistant) -> TvItaliaCoordinator:
    entries = [
        e for e in hass.config_entries.async_loaded_entries(DOMAIN)
        if getattr(e, "runtime_data", None)
    ]
    if not entries:
        raise ServiceValidationError("TV Italia non è configurata o non è ancora pronta.")
    return entries[0].runtime_data


def async_setup_services(hass: HomeAssistant) -> None:
    """Registra le azioni (una volta sola per tutta l'integrazione)."""

    async def set_favorite(call: ServiceCall) -> None:
        coordinator = _coordinator(hass)
        for entity_id in call.data[ATTR_ENTITY_ID]:
            state = hass.states.get(entity_id)
            key = state.attributes.get("channel_key") if state else None
            if key not in CHANNELS_BY_KEY:
                raise ServiceValidationError(f"{entity_id} non è un canale di TV Italia.")
            await coordinator.async_set_favorite(key, call.data.get(ATTR_FAVORITE))

    async def stasera(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass)
        only_fav = call.data[ATTR_ONLY_FAVORITES]
        platform = call.data[ATTR_PLATFORM]
        now = dt_util.utcnow()

        channels = sorted(
            (CHANNELS_BY_KEY[k] for k in coordinator.channel_keys),
            key=lambda c: (c.platform != "dtt", c.number == 0, c.number),
        )
        if platform != "all":
            channels = [c for c in channels if c.platform == platform]
        if only_fav:
            channels = [c for c in channels if c.key in coordinator.favorites]

        programmes = []
        lines = []
        for channel in channels:
            prog = prime_time_programme(coordinator.programmes(channel.key), now)
            if prog is None:
                continue
            start = dt_util.as_local(prog.start).strftime("%H:%M")
            programmes.append(
                {
                    "channel": channel.name,
                    "number": channel.number or None,
                    "title": prog.title,
                    "start": prog.start.isoformat(),
                    "end": prog.stop.isoformat(),
                    "genre": genre_of(prog, channel.genre),
                    "favorite": channel.key in coordinator.favorites,
                }
            )
            star = "★ " if channel.key in coordinator.favorites and not only_fav else ""
            lines.append(f"{star}{channel.name} · {start} {prog.title}")

        return {
            "message": "\n".join(lines) if lines else "Nessuna informazione per stasera.",
            "count": len(programmes),
            "programmes": programmes,
        }

    hass.services.async_register(
        DOMAIN, SERVICE_SET_FAVORITE, set_favorite, schema=SET_FAVORITE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STASERA,
        stasera,
        schema=STASERA_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
