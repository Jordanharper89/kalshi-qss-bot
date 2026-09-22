from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .oi_001_universal_observation_intake import ObservationSourceIdentity, RawObservationEnvelope

BUILD_ID = "OI-005"
OI_005_REVISION = "OI_005_PUBLIC_MARKET_DATA_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

COINBASE_SPOT_BASE_URL = "https://api.coinbase.com/v2/prices"
SUPPORTED_PRODUCTS = ("BTC-USD", "ETH-USD", "SOL-USD")

class PublicMarketDataAdapterError(RuntimeError):
    pass

def _default_transport(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept":"application/json","User-Agent":"Oracle-OI-005/1.0"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise PublicMarketDataAdapterError("market-data response must be a JSON object")
    return value

class PublicMarketDataObservationAdapter:
    read_only = True
    network_allowed = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, *, transport: Callable[[str,float],dict[str,Any]] | None = None, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._transport = transport or _default_transport
        self._timeout_seconds = float(timeout_seconds)
        self._source = ObservationSourceIdentity(
            source_id="coinbase.public.spot",
            source_kind="market_data",
            provider="Coinbase",
            adapter_id="adapter.coinbase.spot.v1",
        )

    @property
    def source_identity(self) -> ObservationSourceIdentity:
        return self._source

    def fetch_spot(self, product_id: str) -> RawObservationEnvelope:
        normalized = str(product_id).strip().upper()
        if normalized not in SUPPORTED_PRODUCTS:
            raise ValueError(f"unsupported product_id: {normalized}")

        url = COINBASE_SPOT_BASE_URL + "/" + quote(normalized, safe="-") + "/spot"
        response = self._transport(url, self._timeout_seconds)
        data = response.get("data")
        if not isinstance(data, dict):
            raise PublicMarketDataAdapterError("Coinbase spot response missing object field 'data'")
        amount = str(data.get("amount","")).strip()
        currency = str(data.get("currency","")).strip().upper()
        try:
            numeric = float(amount)
        except ValueError as exc:
            raise PublicMarketDataAdapterError("Coinbase spot amount is not numeric") from exc
        if numeric <= 0:
            raise PublicMarketDataAdapterError("Coinbase spot amount must be positive")

        base, quote_currency = normalized.split("-",1)
        if currency and currency != quote_currency:
            raise PublicMarketDataAdapterError("Coinbase quote currency mismatch")

        observed_at = datetime.now(timezone.utc)
        return RawObservationEnvelope(
            source=self._source,
            external_observation_id=f"{normalized}:{observed_at.isoformat()}",
            observed_at=observed_at,
            subject=base,
            observation_type="spot_price",
            payload={
                "product_id":normalized,
                "symbol":base,
                "quote_currency":quote_currency,
                "price":amount,
            },
            metadata={
                "venue":"coinbase",
                "source_endpoint":f"/v2/prices/{normalized}/spot",
                "public_market_data":True,
            },
        )

    def fetch_supported_spot(self) -> tuple[RawObservationEnvelope,...]:
        return tuple(self.fetch_spot(product) for product in SUPPORTED_PRODUCTS)

def verify_public_market_data_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-005 must remain read-only")
    if PERSISTENCE_ALLOWED or PUBLICATION_ALLOWED or EXECUTION_ALLOWED or QSERIES_EXECUTION_ALLOWED:
        raise AssertionError("OI-005 forbidden capability enabled")
    return True
