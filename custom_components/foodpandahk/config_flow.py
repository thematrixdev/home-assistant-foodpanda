"""Config flow for Foodpanda HK integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class FoodpandaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Foodpanda HK."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data = {}
        self.entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FoodpandaOptionsFlow:
        """Get the options flow for this handler."""
        return FoodpandaOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("device_token"): str,
                        vol.Required("token"): str,
                        vol.Required("refresh_token"): str,
                        vol.Required("user_agent"): str,
                    }
                ),
            )

        self.data = {
            "device_token": user_input["device_token"],
            "token": user_input["token"],
            "refresh_token": user_input["refresh_token"],
            "user_agent": user_input["user_agent"],
        }
        return self.async_create_entry(
            title="Foodpanda HK",
            data=self.data,
        )


class FoodpandaOptionsFlow(config_entries.OptionsFlow):
    """Handle Foodpanda options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            self._config_entry.data["device_token"] = user_input["device_token"]
            self._config_entry.data["token"] = user_input["token"]
            self._config_entry.data["refresh_token"] = user_input["refresh_token"]
            self._config_entry.data["user_agent"] = user_input["user_agent"]

            return self.async_create_entry(title="Foodpanda HK", data=self._config_entry.data)

        defaults = self._config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("device_token", default=defaults.get("device_token", "")): str,
                    vol.Required("token", default=defaults.get("token", "")): str,
                    vol.Required("refresh_token", default=defaults.get("refresh_token", "")): str,
                    vol.Required("user_agent", default=defaults.get("user_agent", "")): str,
                }
            ),
            errors=errors,
        )
