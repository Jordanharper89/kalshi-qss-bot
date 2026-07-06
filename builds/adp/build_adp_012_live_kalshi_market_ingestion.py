from pathlib import Path

ROOT = Path("qseries_v2")
ADAPTERS = ROOT / "adapters"
ADAPTERS.mkdir(parents=True, exist_ok=True)

ingestion_code = r'''"""
ADP-012 — Live Kalshi Market Ingestion

Purpose:
- Read live Kalshi markets.
- Normalize raw Kalshi market payloads into lightweight Q Series market objects.
- Prepare Oracle for live market analysis.
- Read-only only. No trade execution.

Works with:
- Public unauthenticated market endpoint
- Optional ADP-011/011.1 authenticated session if available
"""

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

try:
    import requests
except Exception:
    requests = None


PRODUCTION_REST_BASE = "https://external-api.kalshi.com/trade-api/v2"
DEMO_REST_BASE = "https://external-api.demo.kalshi.co/trade-api/v2"


class KalshiMarketIngestionError(Exception):
    pass


@dataclass
class LiveKalshiMarket:
    ticker: str
    event_ticker: Optional[str]
    market_type: Optional[str]
    title: str
    subtitle: Optional[str]
    yes_bid: Optional[int]
    yes_ask: Optional[int]
    no_bid: Optional[int]
    no_ask: Optional[int]
    last_price: Optional[int]
    volume: Optional[int]
    open_interest: Optional[int]
    liquidity: Optional[int]
    status: Optional[str]
    close_time: Optional[str]
    expiration_time: Optional[str]
    category: Optional[str]
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveKalshiMarketIngestion:
    def __init__(
        self,
        environment: str = "production",
        auth_session: Any = None,
        event_bus: Any = None,
        timeout_seconds: float = 10.0,
    ):
        self.environment = self._normalize_environment(environment)
        self.auth_session = auth_session
        self.event_bus = event_bus
        self.timeout_seconds = timeout_seconds
        self.last_snapshot: Dict[str, Any] = {
            "status": "empty",
            "markets": [],
            "count": 0,
            "timestamp": None,
        }

        if requests is None:
            raise KalshiMarketIngestionError(
                "Missing dependency: requests. Install with: pip install requests"
            )

    def _normalize_environment(self, environment: str) -> str:
        env = (environment or "production").lower().strip()
        if env in ("prod", "production", "live"):
            return "production"
        if env in ("demo", "sandbox", "test"):
            return "demo"
        raise KalshiMarketIngestionError(
            f"Invalid environment '{environment}'. Use production or demo."
        )

    @property
    def base_url(self) -> str:
        if self.auth_session is not None and hasattr(self.auth_session, "config"):
            return self.auth_session.config.base_url

        if self.environment == "demo":
            return DEMO_REST_BASE

        return PRODUCTION_REST_BASE

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        if self.auth_session is not None and hasattr(self.auth_session, "request"):
            return self.auth_session.request("GET", path, params=params or {})

        url = self.base_url.rstrip("/") + path
        return requests.get(url, params=params or {}, timeout=self.timeout_seconds)

    def normalize_market(self, raw: Dict[str, Any]) -> LiveKalshiMarket:
        return LiveKalshiMarket(
            ticker=raw.get("ticker") or "",
            event_ticker=raw.get("event_ticker"),
            market_type=raw.get("market_type"),
            title=raw.get("title") or raw.get("yes_sub_title") or "",
            subtitle=raw.get("subtitle") or raw.get("yes_sub_title"),
            yes_bid=raw.get("yes_bid"),
            yes_ask=raw.get("yes_ask"),
            no_bid=raw.get("no_bid"),
            no_ask=raw.get("no_ask"),
            last_price=raw.get("last_price"),
            volume=raw.get("volume"),
            open_interest=raw.get("open_interest"),
            liquidity=raw.get("liquidity"),
            status=raw.get("status"),
            close_time=raw.get("close_time"),
            expiration_time=raw.get("expiration_time"),
            category=raw.get("category"),
            raw=raw,
        )

    def fetch_markets(
        self,
        status: str = "open",
        limit: int = 100,
        cursor: Optional[str] = None,
        tickers: Optional[str] = None,
        series_ticker: Optional[str] = None,
        mve_filter: str = "exclude",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": int(limit),
            "mve_filter": mve_filter,
        }

        if status:
            params["status"] = status

        if cursor:
            params["cursor"] = cursor

        if tickers:
            params["tickers"] = tickers

        if series_ticker:
            params["series_ticker"] = series_ticker

        response = self._get("/markets", params=params)

        result = {
            "module": "adp_012_live_kalshi_market_ingestion",
            "status": "unknown",
            "environment": self.environment,
            "base_url": self.base_url,
            "http_status": getattr(response, "status_code", None),
            "count": 0,
            "cursor": None,
            "markets": [],
            "error": None,
            "timestamp": time.time(),
        }

        try:
            if not (200 <= response.status_code < 300):
                result["status"] = "error"
                result["error"] = response.text[:500]
                self.last_snapshot = result
                return result

            payload = response.json()
            raw_markets = payload.get("markets", [])
            normalized = [self.normalize_market(m).to_dict() for m in raw_markets]

            result["status"] = "ok"
            result["count"] = len(normalized)
            result["cursor"] = payload.get("cursor")
            result["markets"] = normalized

            self.last_snapshot = result

            self._emit(
                "adp.kalshi.markets.snapshot",
                {
                    "adapter": "adp.kalshi",
                    "module": "adp_012_live_kalshi_market_ingestion",
                    "status": "ok",
                    "count": len(normalized),
                    "environment": self.environment,
                    "timestamp": result["timestamp"],
                },
            )

            return result

        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            self.last_snapshot = result
            return result

    def fetch_open_markets(self, limit: int = 100) -> Dict[str, Any]:
        return self.fetch_markets(status="open", limit=limit)

    def fetch_tickers(self, tickers: List[str]) -> Dict[str, Any]:
        joined = ",".join([t.strip() for t in tickers if t and t.strip()])
        return self.fetch_markets(status="", tickers=joined, limit=max(1, len(tickers)))

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "adp_012_live_kalshi_market_ingestion",
            "status": "ok",
            "environment": self.environment,
            "base_url": self.base_url,
            "has_auth_session": self.auth_session is not None,
            "last_snapshot_status": self.last_snapshot.get("status"),
            "last_snapshot_count": self.last_snapshot.get("count"),
            "read_only": True,
        }


def build_live_kalshi_market_ingestion(
    environment: str = "production",
    auth_session: Any = None,
    event_bus: Any = None,
) -> LiveKalshiMarketIngestion:
    return LiveKalshiMarketIngestion(
        environment=environment,
        auth_session=auth_session,
        event_bus=event_bus,
    )


if __name__ == "__main__":
    ingestion = build_live_kalshi_market_ingestion(environment="production")
    print(ingestion.diagnostics())
    snapshot = ingestion.fetch_open_markets(limit=5)
    printable = {
        "status": snapshot.get("status"),
        "count": snapshot.get("count"),
        "http_status": snapshot.get("http_status"),
        "cursor": snapshot.get("cursor"),
        "sample_tickers": [m.get("ticker") for m in snapshot.get("markets", [])[:5]],
        "error": snapshot.get("error"),
    }
    print(printable)
'''

test_code = r'''"""
Test ADP-012 Live Kalshi Market Ingestion without hitting Kalshi.

Validates:
- environment handling
- response parsing
- market normalization
- event bus emission
- diagnostics
"""

from qseries_v2.adapters.live_kalshi_market_ingestion import (
    LiveKalshiMarketIngestion,
    KalshiMarketIngestionError,
)


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {
            "markets": [
                {
                    "ticker": "TEST-MARKET-001",
                    "event_ticker": "TEST-EVENT",
                    "market_type": "binary",
                    "title": "Test market title",
                    "subtitle": "Test subtitle",
                    "yes_bid": 44,
                    "yes_ask": 46,
                    "no_bid": 54,
                    "no_ask": 56,
                    "last_price": 45,
                    "volume": 123,
                    "open_interest": 456,
                    "liquidity": 789,
                    "status": "open",
                    "close_time": "2026-12-31T00:00:00Z",
                    "expiration_time": "2026-12-31T00:00:00Z",
                    "category": "Test",
                }
            ],
            "cursor": "next-cursor",
        }


class FakeAuthSession:
    class Config:
        base_url = "https://external-api.demo.kalshi.co/trade-api/v2"

    config = Config()

    def __init__(self):
        self.calls = []

    def request(self, method, path, params=None):
        self.calls.append((method, path, params))
        return FakeResponse()


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_adp_012():
    auth = FakeAuthSession()
    bus = FakeEventBus()

    ingestion = LiveKalshiMarketIngestion(
        environment="demo",
        auth_session=auth,
        event_bus=bus,
    )

    diag = ingestion.diagnostics()
    assert diag["status"] == "ok"
    assert diag["has_auth_session"] is True
    assert diag["read_only"] is True

    snapshot = ingestion.fetch_open_markets(limit=1)

    assert snapshot["status"] == "ok"
    assert snapshot["count"] == 1
    assert snapshot["cursor"] == "next-cursor"
    assert snapshot["markets"][0]["ticker"] == "TEST-MARKET-001"
    assert snapshot["markets"][0]["yes_bid"] == 44
    assert snapshot["markets"][0]["raw"]["ticker"] == "TEST-MARKET-001"
    assert auth.calls[0][0] == "GET"
    assert auth.calls[0][1] == "/markets"
    assert auth.calls[0][2]["status"] == "open"
    assert len(bus.events) >= 1

    try:
        LiveKalshiMarketIngestion(environment="bad-env")
        raise AssertionError("bad environment should fail")
    except KalshiMarketIngestionError:
        pass

    print("[PASS] ADP-012 Live Kalshi Market Ingestion")
    print({
        "diagnostics": diag,
        "snapshot_status": snapshot["status"],
        "snapshot_count": snapshot["count"],
        "sample": snapshot["markets"][0]["ticker"],
    })


if __name__ == "__main__":
    test_adp_012()
'''

init_code = '''try:
    from .live_kalshi_authentication import (
        KalshiAuthConfig,
        KalshiAuthState,
        KalshiAuthError,
        LiveKalshiAuthSession,
        build_live_kalshi_auth_session,
    )
except Exception:
    pass

try:
    from .live_kalshi_market_ingestion import (
        LiveKalshiMarket,
        LiveKalshiMarketIngestion,
        KalshiMarketIngestionError,
        build_live_kalshi_market_ingestion,
    )
except Exception:
    pass
'''

(ADAPTERS / "live_kalshi_market_ingestion.py").write_text(ingestion_code, encoding="utf-8")
(ADAPTERS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_adp_012_live_kalshi_market_ingestion.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" ADP-012 INSTALLER")
print(" Live Kalshi Market Ingestion")
print("========================================")
print("[OK] Wrote qseries_v2\\adapters\\live_kalshi_market_ingestion.py")
print("[OK] Wrote qseries_v2\\adapters\\__init__.py")
print("[OK] Wrote test_adp_012_live_kalshi_market_ingestion.py")
print()
print("[DONE] ADP-012 installed")
print()
print("Run:")
print("python test_adp_012_live_kalshi_market_ingestion.py")
print()
print("Optional live public market check:")
print("python -m qseries_v2.adapters.live_kalshi_market_ingestion")