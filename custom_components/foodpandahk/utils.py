"""Utility functions for Foodpanda HK integration."""
import base64
import json
import logging
import time

import aiohttp

from .const import MOBILE_USER_AGENT, RENEW_TOKEN_ENDPOINT, TOKEN_REFRESH_BUFFER

_LOGGER = logging.getLogger(__name__)


def decode_jwt_expiry(token: str) -> int | None:
    """Decode JWT payload and return the 'expires' timestamp."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("expires")
    except Exception:
        _LOGGER.warning("Failed to decode JWT expiry")
        return None


def token_needs_refresh(token: str) -> bool:
    """Check if the token expires within TOKEN_REFRESH_BUFFER seconds."""
    expires = decode_jwt_expiry(token)
    if expires is None:
        return False
    remaining = expires - int(time.time())
    _LOGGER.debug("Token expires in %ds (%dm)", remaining, remaining // 60)
    return remaining < TOKEN_REFRESH_BUFFER


async def refresh_foodpanda_token(
    device_token: str, refresh_token: str
) -> dict | None:
    """Refresh Foodpanda token using the refresh endpoint.

    Uses a mobile app User-Agent to bypass PerimeterX bot protection
    on www.foodpanda.hk.
    """
    payload = {
        "country": "hk",
        "platform": "b2c",
        "device_token": device_token,
        "refresh_token": refresh_token,
    }
    headers = {
        "Content-Type": "application/json",
        "x-fp-api-key": "volo",
        "User-Agent": MOBILE_USER_AGENT,
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RENEW_TOKEN_ENDPOINT, json=payload, headers=headers
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error(
                        "Token refresh failed (HTTP %s): %s",
                        resp.status,
                        text[:200],
                    )
                    return None
                data = await resp.json()
                _LOGGER.info("Token refreshed successfully")
                return data
    except Exception as err:
        _LOGGER.error("Error refreshing Foodpanda token: %s", err)
        return None
