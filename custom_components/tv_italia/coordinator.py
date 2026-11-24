"""Coordinator: scarica la guida XMLTV e aggiorna le entita' ogni minuto."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CHANNELS_BY_KEY,
    CONF_CHANNELS,
    CONF_EPG_URL,
    CONF_REFRESH_HOURS,
    DEFAULT_CHANNELS,
    DEFAULT_EPG_URL,
    DEFAULT_REFRESH_HOURS,
    DOMAIN,
    PRIME_TIME_HOUR,
    PRIME_TIME_MINUTE,
)
from .epg import ChannelGuide, Programme, parse_xmltv, programme_at, resolve_channel

_LOGGER = logging.getLogger(__name__)

TICK = timedelta(minutes=1)
# Dopo un errore riprova il download non prima di questo intervallo
RETRY_AFTER = timedelta(minutes=15)
LOGO_USER_AGENT = "HomeAssistant-TVItalia/1.4 (https://github.com/massan71/ha-tv-italia)"


class TvItaliaCoordinator(DataUpdateCoordinator[dict[str, ChannelGuide | None]]):
    """Mantiene in memoria il palinsesto dei canali selezionati.

    Il coordinator "batte" ogni minuto cosi' le entita' aggiornano il programma
    in onda; il file XMLTV viene riscaricato solo ogni `refresh_hours`.
    """

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=TICK,
            config_entry=entry,
        )
        self._last_download: datetime | None = None
        self._last_attempt: datetime | None = None
        self._logos: dict[str, str | None] = {}
        self._favorites_store: Store[list[str]] = Store(hass, 1, f"{DOMAIN}.favorites")
        self.favorites: set[str] = set()

    async def async_load_favorites(self) -> None:
        """Carica i canali preferiti salvati (condivisi tra tutti i dispositivi)."""
        self.favorites = set(await self._favorites_store.async_load() or [])

    async def async_set_favorite(self, key: str, favorite: bool | None = None) -> bool:
        """Aggiunge/toglie un preferito; con favorite=None lo inverte."""
        if favorite is None:
            favorite = key not in self.favorites
        if favorite:
            self.favorites.add(key)
        else:
            self.favorites.discard(key)
        await self._favorites_store.async_save(sorted(self.favorites))
        self.async_update_listeners()
        return favorite

    def programmes(self, key: str) -> list[Programme]:
        guide = (self.data or {}).get(key)
        return guide.programmes if guide else []

    def logo(self, key: str) -> str | None:
        """Logo funzionante del canale (verificato all'ultimo download)."""
        return self._logos.get(key)

    async def _async_pick_logos(
        self, guides: dict[str, ChannelGuide], result: dict[str, ChannelGuide | None]
    ) -> dict[str, str | None]:
        """Sceglie per ogni canale il primo logo che si carica davvero.

        Alcuni loghi della guida rispondono 403/404: si provano in ordine il
        logo del palinsesto usato, quelli degli ID alternativi e infine il logo
        di riserva definito in const.py.
        """
        session = async_get_clientsession(self.hass)
        checked: dict[str, asyncio.Task[bool]] = {}

        async def works(url: str) -> bool:
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": LOGO_USER_AGENT},
                ) as resp:
                    return resp.status == 200 and resp.content_type.startswith("image/")
            except (aiohttp.ClientError, TimeoutError):
                return False

        async def pick(key: str) -> str | None:
            channel = CHANNELS_BY_KEY[key]
            candidates: list[str] = []
            if (guide := result.get(key)) and guide.icon:
                candidates.append(guide.icon)
            candidates += [
                guides[i].icon for i in channel.epg_ids if i in guides and guides[i].icon
            ]
            if channel.logo:
                candidates.append(channel.logo)
            for url in dict.fromkeys(candidates):
                if url not in checked:
                    checked[url] = asyncio.ensure_future(works(url))
                if await checked[url]:
                    return url
            return None

        keys = list(result)
        logos = await asyncio.gather(*(pick(k) for k in keys))
        return dict(zip(keys, logos))

    @property
    def options(self) -> dict:
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def channel_keys(self) -> list[str]:
        keys = self.options.get(CONF_CHANNELS, DEFAULT_CHANNELS)
        return [k for k in keys if k in CHANNELS_BY_KEY]

    @property
    def last_download(self) -> datetime | None:
        return self._last_download

    def _needs_download(self, now: datetime) -> bool:
        if not self.data:
            return True
        refresh = timedelta(hours=self.options.get(CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS))
        if self._last_download and now - self._last_download < refresh:
            return False
        # Evita di martellare il server dopo un download fallito
        return not (self._last_attempt and now - self._last_attempt < RETRY_AFTER)

    async def _async_update_data(self) -> dict[str, ChannelGuide | None]:
        now = dt_util.utcnow()
        if not self._needs_download(now):
            return self.data

        self._last_attempt = now
        url = self.options.get(CONF_EPG_URL, DEFAULT_EPG_URL)
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                resp.raise_for_status()
                raw = await resp.read()
        except (aiohttp.ClientError, TimeoutError) as err:
            if self.data:
                _LOGGER.warning("Download guida TV fallito, uso i dati in cache: %s", err)
                return self.data
            raise UpdateFailed(f"Impossibile scaricare la guida TV da {url}: {err}") from err

        try:
            guides = await self.hass.async_add_executor_job(
                parse_xmltv, raw, now - timedelta(hours=6), now + timedelta(days=2)
            )
        except Exception as err:  # XML malformato
            if self.data:
                _LOGGER.warning("Guida TV non valida, uso i dati in cache: %s", err)
                return self.data
            raise UpdateFailed(f"Guida TV non valida: {err}") from err

        result: dict[str, ChannelGuide | None] = {}
        for key in self.channel_keys:
            channel = CHANNELS_BY_KEY[key]
            guide = resolve_channel(guides, channel.epg_ids, channel.name)
            if guide is None:
                _LOGGER.debug("Nessun palinsesto trovato per %s", channel.name)
            result[key] = guide

        self._logos = await self._async_pick_logos(guides, result)
        self._last_download = now
        _LOGGER.debug(
            "Guida TV aggiornata: %d/%d canali con palinsesto, %d con logo",
            sum(1 for g in result.values() if g),
            len(result),
            sum(1 for u in self._logos.values() if u),
        )
        return result


def prime_time_programme(programmes: list[Programme], now: datetime) -> Programme | None:
    """Programma in onda alle 21:30 di stasera (fino alle 3 vale la sera prima)."""
    local_now = dt_util.as_local(now)
    target = local_now.replace(
        hour=PRIME_TIME_HOUR, minute=PRIME_TIME_MINUTE, second=0, microsecond=0
    )
    if local_now.hour < 3:
        target -= timedelta(days=1)
    return programme_at(programmes, target)
