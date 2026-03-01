"""Constants for the Foodpanda HK integration."""

DOMAIN = "foodpandahk"

# API Endpoints
TRACKING_ENDPOINT = "https://hk.fd-api.com/api/v5/tracking/active-orders?order_status_variation=Variation1"
RENEW_TOKEN_ENDPOINT = "https://www.foodpanda.hk/login/new/api/refresh-token"

# Mobile UA bypasses PerimeterX bot protection on www.foodpanda.hk
MOBILE_USER_AGENT = "Foodpanda/24.5.0 (iPhone; iOS 17.4; Scale/3.00)"

# Refresh token before it expires (seconds)
TOKEN_REFRESH_BUFFER = 300
