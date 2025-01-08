"""Foodpanda HK sensor platform."""
from __future__ import annotations

import logging
import aiohttp
import json
from datetime import timedelta
from .utils import refresh_foodpanda_token

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    TRACKING_ENDPOINT,
    RENEW_TOKEN_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Foodpanda HK sensor."""

    coordinator = FoodpandaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = [FoodpandaWaybillSensor(coordinator)]
    
    async_add_entities(entities, True)


class FoodpandaCoordinator(DataUpdateCoordinator):
    """Foodpanda data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry

    async def _async_update_data(self):
        """Fetch data from Foodpanda using the tracking endpoint and token authentication."""
        config = self.entry.data
        device_token_val = config.get("device_token", "")
        token = config.get("token", "")
        refresh_token_val = config.get("refresh_token", "")
        user_agent_val = config.get("user_agent", "")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-fp-api-key": "volo",
            "User-Agent": user_agent_val,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(TRACKING_ENDPOINT, headers=headers) as response:
                    if response.status == 401:
                        # Token expired, refresh it
                        refresh_result = await refresh_foodpanda_token(device_token_val, refresh_token_val, user_agent_val)
                        if refresh_result and "access_token" in refresh_result and "refresh_token" in refresh_result:
                            # Update tokens in config entry and persist
                            new_data = dict(self.entry.data)
                            new_data["token"] = refresh_result["access_token"]
                            new_data["refresh_token"] = refresh_result["refresh_token"]
                            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                            # Retry with new token
                            headers["Authorization"] = f"Bearer {refresh_result['access_token']}"
                            async with session.get(TRACKING_ENDPOINT, headers=headers) as retry_response:
                                retry_response.raise_for_status()
                                data = await retry_response.json()
                                _LOGGER.debug("Foodpanda tracking API response (after refresh): %s", data)
                                return data
                        else:
                            _LOGGER.error("Failed to refresh token: %s", refresh_result)
                            return None
                    response.raise_for_status()
                    data = await response.json()
                    _LOGGER.debug("Foodpanda tracking API response: %s", data)
                    return data
        except Exception as err:
            _LOGGER.error("Error updating Foodpanda data: %s", err)
            return None


class FoodpandaWaybillSensor(CoordinatorEntity, SensorEntity):
    """Foodpanda Waybill sensor."""

    def __init__(self, coordinator: FoodpandaCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Foodpanda"
        self._attr_unique_id = "foodpanda"

    @property
    def native_value(self):
        """Return the name of the current active status in active_orders[0][status_messages][titles]."""
        if self.coordinator.data is None:
            return None
        try:
            active_orders = self.coordinator.data.get("data", {}).get("active_orders", [])
            if not active_orders:
                return "IDLE"
            titles = active_orders[0].get("status_messages", {}).get("titles", [])
            for title in titles:
                if title.get("active"):
                    return title.get("name")
            return "IDLE"
        except Exception as err:
            _LOGGER.error("Error extracting active status name: %s", err)
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes: everything inside the 'data' key of the response."""
        if self.coordinator.data is None:
            return {}
        try:
            # Return all items inside 'data' as attributes
            return dict(self.coordinator.data.get("data", {}))
        except Exception as err:
            _LOGGER.error("Error extracting sensor attributes: %s", err)
            return {}
