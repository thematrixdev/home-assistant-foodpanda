"""Foodpanda HK sensor platform."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


from .const import DOMAIN, MOBILE_USER_AGENT, TRACKING_ENDPOINT
from .utils import refresh_foodpanda_token, token_needs_refresh

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
    async_add_entities([FoodpandaWaybillSensor(coordinator)], True)


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
        self._last_known_data = None

    async def _refresh_and_update_tokens(self) -> str | None:
        """Refresh tokens and persist to config entry. Returns new access token or None."""
        config = self.entry.data
        result = await refresh_foodpanda_token(
            config.get("device_token", ""),
            config.get("refresh_token", ""),
        )
        if result and "access_token" in result and "refresh_token" in result:
            new_data = dict(self.entry.data)
            new_data["token"] = result["access_token"]
            new_data["refresh_token"] = result["refresh_token"]
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            return result["access_token"]
        _LOGGER.error("Failed to refresh token: %s", result)
        return None

    async def _async_update_data(self):
        """Fetch data from Foodpanda tracking API."""
        token = self.entry.data.get("token", "")

        # Proactive refresh if token is about to expire
        if token_needs_refresh(token):
            _LOGGER.info("Token expiring soon, refreshing proactively")
            new_token = await self._refresh_and_update_tokens()
            if new_token:
                token = new_token

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "x-fp-api-key": "volo",
            "User-Agent": MOBILE_USER_AGENT,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(TRACKING_ENDPOINT, headers=headers) as response:
                    if response.status == 401:
                        _LOGGER.warning("Got 401, refreshing token")
                        new_token = await self._refresh_and_update_tokens()
                        if not new_token:
                            raise UpdateFailed("Token refresh failed after 401")
                        headers["Authorization"] = f"Bearer {new_token}"
                        async with session.get(
                            TRACKING_ENDPOINT, headers=headers
                        ) as retry_response:
                            retry_response.raise_for_status()
                            data = await retry_response.json()
                            _LOGGER.debug("Tracking response (after refresh): %s", data)
                            self._last_known_data = data
                            return data
                    response.raise_for_status()
                    data = await response.json()
                    _LOGGER.debug("Tracking response: %s", data)
                    self._last_known_data = data
                    return data
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.warning("Network error, using cached data: %s", err)
            return self._last_known_data


class FoodpandaWaybillSensor(CoordinatorEntity, SensorEntity):
    """Foodpanda Waybill sensor."""

    def __init__(self, coordinator: FoodpandaCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Foodpanda"
        self._attr_unique_id = "foodpanda"

    @property
    def native_value(self):
        """Return the name of the current active status."""
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
            _LOGGER.error("Error extracting active status: %s", err)
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        try:
            return dict(self.coordinator.data.get("data", {}))
        except Exception as err:
            _LOGGER.error("Error extracting sensor attributes: %s", err)
            return {}
