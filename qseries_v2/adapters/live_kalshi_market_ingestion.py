"""
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
