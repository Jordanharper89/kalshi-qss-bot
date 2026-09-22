from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .oi_001_universal_observation_intake import ObservationSourceIdentity, RawObservationEnvelope

BUILD_ID = "OI-004"
OI_004_REVISION = "OI_004_KALSHI_UNIVERSAL_OBSERVATION_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

class KalshiObservationAdapterError(RuntimeError):
    pass

def _default_transport(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Oracle-OI-004/1.0"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise KalshiObservationAdapterError("Kalshi response must be a JSON object")
    return value

class KalshiUniversalObservationAdapter:
    read_only = True
    network_allowed = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, *, transport: Callable[[str, float], dict[str, Any]] | None = None, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._transport = transport or _default_transport
        self._timeout_seconds = float(timeout_seconds)
        self._source = ObservationSourceIdentity(
            source_id="kalshi.public",
            source_kind="market_venue",
            provider="Kalshi",
            adapter_id="adapter.kalshi.v1",
        )

    @property
    def source_identity(self) -> ObservationSourceIdentity:
        return self._source

    def fetch_markets(self, *, limit: int = 100, status: str = "open", cursor: str | None = None) -> tuple[RawObservationEnvelope, ...]:
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 through 1000")
        normalized_status = str(status).strip().lower()
        if normalized_status not in {"unopened", "open", "closed", "settled"}:
            raise ValueError("unsupported Kalshi market status")
        params: dict[str, Any] = {"limit": limit, "status": normalized_status}
        if cursor:
            params["cursor"] = str(cursor).strip()
        response = self._transport(KALSHI_BASE_URL + "/markets?" + urlencode(params), self._timeout_seconds)
        markets = response.get("markets", ())
        if not isinstance(markets, list):
            raise KalshiObservationAdapterError("Kalshi markets response missing list field 'markets'")
        observed_at = datetime.now(timezone.utc)
        envelopes = []
        for market in markets:
            if not isinstance(market, dict):
                raise KalshiObservationAdapterError("Kalshi market item must be an object")
            ticker = str(market.get("ticker", "")).strip()
            title = str(market.get("title") or market.get("subtitle") or ticker).strip()
            if not ticker or not title:
                raise KalshiObservationAdapterError("Kalshi market requires ticker and title")
            envelopes.append(
                RawObservationEnvelope(
                    source=self._source,
                    external_observation_id=f"{ticker}:{observed_at.isoformat()}",
                    observed_at=observed_at,
                    subject=title,
                    observation_type="market_snapshot",
                    payload=dict(market),
                    metadata={
                        "venue": "kalshi",
                        "market_ticker": ticker,
                        "market_status": normalized_status,
                        "source_endpoint": "/markets",
                    },
                )
            )
        return tuple(sorted(envelopes, key=lambda item: (str(item.metadata.get("market_ticker", "")), item.external_observation_id)))

def verify_kalshi_observation_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-004 must remain read-only")
    if PERSISTENCE_ALLOWED or PUBLICATION_ALLOWED or EXECUTION_ALLOWED or QSERIES_EXECUTION_ALLOWED:
        raise AssertionError("OI-004 forbidden capability enabled")
    return True
