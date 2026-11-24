"""Coordinator: scarica la guida XMLTV e aggiorna le entita' ogni minuto."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
)
from .epg import ChannelGuide, parse_xmltv, resolve_channel

_LOGGER = logging.getLogger(__name__)

TICK = timedelta(minutes=1)
# Dopo un errore riprova il download non prima di questo intervallo
RETRY_AFTER = timedelta(minutes=15)


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

        self._last_download = now
        _LOGGER.debug(
            "Guida TV aggiornata: %d/%d canali con palinsesto",
            sum(1 for g in result.values() if g),
            len(result),
        )
        return result
