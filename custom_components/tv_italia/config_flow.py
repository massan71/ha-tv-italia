"""Config flow per TV Italia."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CHANNELS,
    CONF_CHANNELS,
    CONF_EPG_URL,
    CONF_REFRESH_HOURS,
    DEFAULT_CHANNELS,
    DEFAULT_EPG_URL,
    DEFAULT_REFRESH_HOURS,
    DOMAIN,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    options = [
        SelectOptionDict(
            value=c.key,
            label=f"{c.number} · {c.name}" if c.number else c.name,
        )
        for c in sorted(
            CHANNELS, key=lambda c: (c.platform != "dtt", c.number == 0, c.number)
        )
    ]
    return vol.Schema(
        {
            vol.Required(
                CONF_CHANNELS, default=defaults.get(CONF_CHANNELS, DEFAULT_CHANNELS)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options, multiple=True, mode=SelectSelectorMode.LIST
                )
            ),
            vol.Required(
                CONF_EPG_URL, default=defaults.get(CONF_EPG_URL, DEFAULT_EPG_URL)
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
            vol.Required(
                CONF_REFRESH_HOURS,
                default=defaults.get(CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1, max=24, step=1, mode=NumberSelectorMode.BOX,
                    unit_of_measurement="h",
                )
            ),
        }
    )


def _validate(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not user_input.get(CONF_CHANNELS):
        errors[CONF_CHANNELS] = "no_channels"
    if not str(user_input.get(CONF_EPG_URL, "")).startswith(("http://", "https://")):
        errors[CONF_EPG_URL] = "invalid_url"
    return errors


class TvItaliaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione iniziale."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                user_input[CONF_REFRESH_HOURS] = int(user_input[CONF_REFRESH_HOURS])
                return self.async_create_entry(title="TV Italia", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TvItaliaOptionsFlow()


class TvItaliaOptionsFlow(OptionsFlow):
    """Permette di cambiare canali e sorgente della guida."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                user_input[CONF_REFRESH_HOURS] = int(user_input[CONF_REFRESH_HOURS])
                return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(user_input or current), errors=errors
        )
