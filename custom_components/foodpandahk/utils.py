"""Utility functions for Foodpanda HK integration."""
import hashlib
import json
import base64
import aiohttp

def decode_secret(encoded: str) -> str:
    """Decode base64 encoded secret."""
    return base64.b64decode(encoded).decode('utf-8')

BODY_SECRET = "TndwQDlCMlZPUE1mUFFpNEI5Tn4mUEpGUVlxNkNTT3c="
FIRST_SECRET = "ZXYyV01CfnE0YSZheVNEdkVORDU3SThCK2duVkReQG8="
SECOND_SECRET = "NmhuOFRUZWtPcEVLOTJhJSt1eWdHQWxoaSRiYSRZNjI="

def md5_hex(string: str) -> str:
    return hashlib.md5(string.encode("utf-8")).hexdigest()

def generate_syttoken(
    body_json: str,
    device_id: str,
    client_version: str,
    time_interval: str,
    region_code: str,
    language_code: str,
    js_bundle: str,
) -> str:
    body_secret = decode_secret(BODY_SECRET)
    body_hash = md5_hex(body_json + "&" + body_secret)

    first_secret = decode_secret(FIRST_SECRET)
    raw_str1 = (
        device_id
        + time_interval
        + client_version
        + first_secret
        + region_code
        + language_code
        + body_hash
        + js_bundle
    )

    md5_1 = md5_hex(raw_str1 + "&" + first_secret)

    second_secret = decode_secret(SECOND_SECRET)
    return md5_hex(md5_1 + "&" + second_secret)

async def refresh_foodpanda_token(device_token: str, refresh_token: str, user_agent: str) -> dict | None:
    """
    Refresh Foodpanda token using the refresh endpoint.
    Returns a dict with new tokens and expiry info, or None on error.
    """
    from .const import RENEW_TOKEN_ENDPOINT
    payload = {
        "country": "hk",
        "platform": "b2c",
        "device_token": device_token,
        "refresh_token": refresh_token,
    }
    headers = {
        "Content-Type": "application/json",
        "x-fp-api-key": "volo",
        "User-Agent": user_agent,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(RENEW_TOKEN_ENDPOINT, json=payload, headers=headers) as resp:
                text = await resp.text()
                try:
                    resp.raise_for_status()
                except Exception as http_err:
                    print(f"Token refresh HTTP error: {http_err}, status: {resp.status}, response: {text}")
                    return None
                try:
                    return await resp.json()
                except Exception as json_err:
                    print(f"Token refresh JSON decode error: {json_err}, raw response: {text}")
                    return None
    except Exception as err:
        print(f"Error refreshing Foodpanda token: {err}, payload: {payload}, headers: {headers}")
        return None
