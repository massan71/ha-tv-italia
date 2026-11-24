"""Sensori: un sensore per canale con il programma in onda."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import TvItaliaConfigEntry
from .const import CHANNELS_BY_KEY, DOMAIN, UPCOMING_COUNT, Channel
from .coordinator import TvItaliaCoordinator, prime_time_programme
from .epg import Programme, current_and_upcoming, genre_of


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TvItaliaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    keys = coordinator.channel_keys

    # Rimuove le entita' dei canali deselezionati nelle opzioni
    registry = er.async_get(hass)
    wanted = {f"{entry.entry_id}_{k}" for k in keys}
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.unique_id not in wanted:
            registry.async_remove(reg_entry.entity_id)

    # Ordine del telecomando: Rai 1, Rai 2, Rai 3, Rete 4, ...
    channels = sorted(
        (CHANNELS_BY_KEY[k] for k in keys),
        key=lambda c: (c.platform != "dtt", c.number == 0, c.number),
    )
    async_add_entities(TvChannelSensor(coordinator, c) for c in channels)


def _short(prog: Programme | None, default_genre: str | None) -> dict[str, Any] | None:
    if prog is None:
        return None
    return {
        "title": prog.title,
        "subtitle": prog.subtitle,
        "start": prog.start.isoformat(),
        "end": prog.stop.isoformat(),
        "categories": prog.categories,
        "genre": genre_of(prog, default_genre),
    }


class TvChannelSensor(CoordinatorEntity[TvItaliaCoordinator], SensorEntity):
    """Mostra il titolo del programma in onda su un canale."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:television-classic"
    # La lista dei prossimi programmi e le descrizioni non servono nello storico
    _unrecorded_attributes = frozenset(
        {"upcoming", "description", "prime_time", "image", "channel_logo"}
    )

    def __init__(self, coordinator: TvItaliaCoordinator, channel: Channel) -> None:
        super().__init__(coordinator)
        self._channel = channel
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{channel.key}"
        # Il numero davanti al nome fa si' che Home Assistant, che ordina le
        # entita' alfabeticamente, le mostri nell'ordine del telecomando.
        # Tre cifre perche' i canali Sky arrivano a 310 (001 < 020 < 108).
        self._attr_name = (
            f"{channel.number:03d} · {channel.name}" if channel.number else channel.name
        )
        self.entity_id = f"sensor.tv_{channel.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Guida TV Italia",
            manufacturer="TV Italia",
            model="Guida XMLTV",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _programmes(self) -> list[Programme]:
        return self.coordinator.programmes(self._channel.key)

    @property
    def available(self) -> bool:
        return super().available and bool(self._programmes)

    @property
    def native_value(self) -> str | None:
        current, _ = current_and_upcoming(self._programmes, dt_util.utcnow(), 0)
        if current is None:
            return "Nessuna informazione"
        return current.title[:255]

    @property
    def entity_picture(self) -> str | None:
        return self.coordinator.logo(self._channel.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        now = dt_util.utcnow()
        current, upcoming = current_and_upcoming(self._programmes, now, UPCOMING_COUNT)

        attrs: dict[str, Any] = {
            "source": DOMAIN,
            "channel_key": self._channel.key,
            "channel_name": self._channel.name,
            "channel_number": self._channel.number or None,
            "channel_group": self._channel.group,
            "channel_platform": self._channel.platform,
            "channel_logo": self.coordinator.logo(self._channel.key),
            "favorite": self._channel.key in self.coordinator.favorites,
        }
        genre = self._channel.genre
        if current:
            duration = (current.stop - current.start).total_seconds()
            elapsed = (now - current.start).total_seconds()
            attrs.update(
                {
                    "subtitle": current.subtitle,
                    "description": current.description,
                    "categories": current.categories,
                    "genre": genre_of(current, genre),
                    "episode": current.episode,
                    "image": current.icon,
                    "start": current.start.isoformat(),
                    "end": current.stop.isoformat(),
                    "progress": round(max(0, min(100, elapsed / duration * 100)))
                    if duration > 0
                    else None,
                    "remaining_minutes": max(0, round((current.stop - now).total_seconds() / 60)),
                }
            )
        nxt = upcoming[0] if upcoming else None
        attrs["next_title"] = nxt.title if nxt else None
        attrs["next_start"] = nxt.start.isoformat() if nxt else None
        attrs["upcoming"] = [_short(p, genre) for p in upcoming]
        attrs["prime_time"] = _short(prime_time_programme(self._programmes, now), genre)
        if self.coordinator.last_download:
            attrs["guide_updated"] = self.coordinator.last_download.isoformat()
        attrs["guide_source"] = self.coordinator.channel_source.get(self._channel.key)
        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
