from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import kalshi_rest_get
from .oad_024_physical_websocket import probe_kalshi_websocket

OAD_025_BUILD_ID="OAD-025"
OAD_025_REVISION="OAD_025_LIVE_KALSHI_ACQUISITION_GATE_CORRECTION_V2"

@dataclass(frozen=True)
class LiveKalshiAcquisitionResult:
    credential_ready: bool
    authenticated_rest_live: bool
    open_markets_seen: int
    websocket_connected: bool
    websocket_subscribed: bool
    websocket_messages: int
    websocket_message_types: tuple[str, ...]
    certified_live: bool
    result_hash: str

def select_live_probe_tickers(markets, limit=5):
    tickers=[]
    for market in markets:
        ticker=str(market.get("ticker","")).strip()
        status=str(market.get("status","")).strip().lower()
        if ticker and status in ("open","active"):
            tickers.append(ticker)
        if len(tickers)>=int(limit):
            break
    return tuple(tickers)

def run_live_kalshi_acquisition_probe(root=None, timeout_seconds=10, progress=None):
    emit = progress or (lambda _msg: None)

    emit("[1/5] Loading Kalshi credentials")
    credentials=load_kalshi_credentials(root=root)
    emit("[PASS] Credentials loaded locally")

    emit("[2/5] Verifying authenticated Kalshi REST")
    auth=kalshi_rest_get(credentials,"/portfolio/balance",{},timeout_seconds)
    if auth.status_code != 200:
        raise RuntimeError("Authenticated Kalshi REST verification failed")
    emit("[PASS] Authenticated REST status=200")

    emit("[3/5] Fetching live/open Kalshi market page")
    response=kalshi_rest_get(
        credentials,
        "/markets",
        {"limit":1000,"status":"open"},
        timeout_seconds,
    )
    markets=tuple(response.body.get("markets",()))
    tickers=select_live_probe_tickers(markets,5)
    if not tickers:
        raise RuntimeError("No open Kalshi markets available for live WebSocket probe")
    emit(f"[PASS] Open markets fetched={len(markets)} probe_tickers={len(tickers)}")

    emit("[4/5] Connecting authenticated Kalshi WebSocket")
    ws=probe_kalshi_websocket(
        credentials,
        tickers,
        channels=("ticker","trade"),
        max_messages=2,
        timeout_seconds=timeout_seconds,
    )
    if not ws.connected:
        raise RuntimeError("Kalshi WebSocket did not connect")
    emit("[PASS] WebSocket connected")

    if not ws.subscribed:
        raise RuntimeError("Kalshi WebSocket subscription was not acknowledged")
    emit("[PASS] WebSocket subscription acknowledged")

    emit("[5/5] Confirming live WebSocket traffic")
    if ws.messages_received < 1:
        raise RuntimeError("No Kalshi WebSocket messages received")
    emit(f"[PASS] WebSocket messages={ws.messages_received} types={ws.message_types}")

    raw={
        "credential_ready":True,
        "authenticated_rest_live":True,
        "open_markets_seen":len(markets),
        "websocket_connected":ws.connected,
        "websocket_subscribed":ws.subscribed,
        "websocket_messages":ws.messages_received,
        "websocket_message_types":ws.message_types,
    }
    certified=bool(
        raw["credential_ready"]
        and raw["authenticated_rest_live"]
        and raw["open_markets_seen"]>0
        and raw["websocket_connected"]
        and raw["websocket_subscribed"]
        and raw["websocket_messages"]>0
    )
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()

    return LiveKalshiAcquisitionResult(
        True,True,len(markets),ws.connected,ws.subscribed,
        ws.messages_received,tuple(ws.message_types),certified,h
    )

def build_oad_025_certification_manifest():
    return MappingProxyType({
        "build_id":OAD_025_BUILD_ID,
        "revision":OAD_025_REVISION,
        "startup_path":"credentials_authenticated_rest_open_markets_websocket_live_first",
        "historical_reconciliation_blocks_live_startup":False,
        "physical_rest_required":True,
        "physical_websocket_required":True,
        "subscription_ack_required":True,
        "credentials_persisted":False,
        "execution":False,
        "next_capability":"bind_physical_kalshi_adapter_into_oracle_live_runtime_and_live_shadow",
    })

def verify_oad_025_live_kalshi_acquisition_certification_gate():
    m=build_oad_025_certification_manifest()
    return (
        m["physical_rest_required"]
        and m["physical_websocket_required"]
        and m["subscription_ack_required"]
        and not m["historical_reconciliation_blocks_live_startup"]
        and not m["credentials_persisted"]
        and not m["execution"]
    )
