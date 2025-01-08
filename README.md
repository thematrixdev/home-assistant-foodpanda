# Foodpanda (HK) Home-Assistant Custom-Component

## Add to HACS

1. Setup `HACS` https://hacs.xyz/docs/setup/prerequisites
2. In `Home Assistant`, click `HACS` on the menu on the left
3. Select `integrations`
4. Click the menu button in the top right hand corner
5. Choose `custom repositories`
6. Enter `https://github.com/thematrixdev/home-assistant-foodpanda` and choose `Integration`, click `ADD`
7. Find and click on `Foodpanda HK` in the `custom repositories` list
8. Click the `DOWNLOAD` button in the bottom right hand corner

## Install

1. Go to `Settings`, `Devices and Services`
2. Click the `Add Integration` button
3. Search `Foodpanda HK`
4. Go through the configuration flow
5. Restart Home Assistant

## Configuration

1. Go to [Foodpanda (HK)](https://www.foodpanda.hk) using Google Chrome on your computer
2. Login to your account
3. Press `F12` on your keyboard, or right-click anywhere on the page and select `Inspect`
4. Go to `Application` tab
5. Select `Cookies` under `Storage` section
6. Select `https://www.foodpanda.hk`
7. Copy the `device_token`, `refresh_token` and `token` values
8. Go to `Network` tab
9. Click on any name, and copy `User-Agent` from `Request Headers`

## Important Note

- Logging out from Foodpanda web page will log you out from this integration

## Debug

### Basic

- On Home Assistant, go to `Settigns` -> `Logs`
- Search `Foodpanda HK`

### Advanced

- Add these lines to `configuration.yaml`

```yaml
logger:
  default: info
  logs:
    custom_components.foodpandahk: debug
```

- Restart Home Assistant
- On Home Assistant, go to `Settigns` -> `Logs`
- Search `Foodpanda HK`
- Click the `LOAD FULL LOGS` button

## Support

- Open an issue on GitHub
- Specify:
    - What's wrong
    - Home Assistant version
    - Foodpanda custom-integration version
    - Logs

## Unofficial support

- Telegram Group https://t.me/smarthomehk

## Tested on

- Home Assistant Container 2025.6.3
