"""
ADP-010 Live Kalshi Client

Foundation for live Kalshi API connectivity.

NOTE:
No authentication is implemented yet.
This build establishes the client architecture only.
"""

import requests


class LiveKalshiClient:

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, timeout=10):
        self.timeout = timeout

    def health(self):
        return {
            "status": "ready",
            "client": "LiveKalshiClient",
            "base_url": self.BASE_URL,
            "authenticated": False,
            "executes_trades": False,
        }

    def build_url(self, endpoint):
        endpoint = endpoint.lstrip("/")
        return f"{self.BASE_URL}/{endpoint}"

    def get(self, endpoint, params=None):
        url = self.build_url(endpoint)

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()


live_kalshi_client = LiveKalshiClient()
