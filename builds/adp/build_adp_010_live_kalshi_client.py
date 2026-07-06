"""
build_adp_010_live_kalshi_client.py
ADP-010 Live Kalshi Client Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
ADP = ROOT / "qseries_v2" / "adapters"


def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")


client_code = '''"""
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
'''

test_code = '''from qseries_v2.adapters.live_kalshi_client import live_kalshi_client

health = live_kalshi_client.health()

assert health["status"] == "ready"
assert health["authenticated"] is False
assert health["executes_trades"] is False

url = live_kalshi_client.build_url("markets")

assert url.endswith("/markets")

print("[PASS] ADP-010 Live Kalshi Client")
print(health)
print(url)
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
from .kalshi_oracle_bridge import *
from .kalshi_analysis_bridge import *
from .kalshi_diagnostics import *
from .kalshi_bootstrap import *
from .adapter_manager import *
from .adapter_manager_bootstrap import *
from .live_kalshi_client import *
'''

print("=" * 40)
print(" ADP-010 INSTALLER")
print(" Live Kalshi Client")
print("=" * 40)

write(ADP / "live_kalshi_client.py", client_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_010_live_kalshi_client.py", test_code)

print("\n[DONE] ADP-010 installed")
print("\nRun:")
print("python test_adp_010_live_kalshi_client.py")