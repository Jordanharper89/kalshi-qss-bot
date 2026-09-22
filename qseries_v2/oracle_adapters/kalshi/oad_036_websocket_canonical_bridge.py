from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json

from qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap import freeze_trade

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    RawSourceObservation,
    CanonicalObservation,
)

OAD_036_BUILD_ID="OAD-036"
OAD_036_REVISION="OAD_036_KALSHI_WEBSOCKET_TO_OLA_CANONICAL_OBSERVATION_BRIDGE_V1"
SOURCE_ID="source.kalshi.market_data"
ADAPTER_ID="adapter.oracle.kalshi.websocket.live"

def _canonical_json(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def build_ola_canonical_observation_from_websocket(raw_message,*,received_at,acquisition_batch_id):
    if not isinstance(raw_message,dict):
        raise TypeError("raw_message must be dict")
    if not isinstance(received_at,datetime) or received_at.tzinfo is None:
        raise ValueError("received_at must be timezone-aware datetime")
    received_at=received_at.astimezone(timezone.utc)
    typ=str(raw_message.get("type","")).strip()
    if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"):
        raise ValueError("unsupported live market-data type")
    msg=raw_message.get("msg") or {}
    if not isinstance(msg,dict):
        raise ValueError("msg must be mapping")
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()
    if not ticker:
        raise ValueError("market ticker required")
    sid=int(raw_message.get("sid",0))
    seq=int(raw_message.get("seq",0))
    raw_hash=sha256(_canonical_json(raw_message).encode("utf-8")).hexdigest()
    source_observation_id=f"kalshi.websocket.{typ}.{ticker}.{sid}.{seq}.{raw_hash[:16]}"
    payload={
        "source_market_id":ticker,
        "event_type":typ,
        "sid":sid,
        "seq":seq,
        "message":msg,
        "raw_message_hash":raw_hash,
    }
    provenance={
        "source_id":SOURCE_ID,
        "adapter_id":ADAPTER_ID,
        "transport":"websocket",
        "read_only":True,
    }
    raw=RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=received_at,
        observation_type=typ,
        payload=payload,
        provenance=provenance,
    )
    observation=CanonicalObservation.create(
        source_id=SOURCE_ID,
        raw_observation=raw,
        acquired_at=received_at,
        acquisition_batch_id=str(acquisition_batch_id),
    )
    if typ in ("trade","ticker"):
        freeze_trade(
            raw_message,
            received_at.timestamp(),
            observation.observation_id,
            Path.cwd(),
        )
    return observation

def verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge():
    t=datetime(2026,8,13,20,0,0,tzinfo=timezone.utc)
    raw={"type":"ticker","sid":1,"seq":2,"msg":{"market_ticker":"KXTEST","yes_bid_dollars":"0.50"}}
    a=build_ola_canonical_observation_from_websocket(raw,received_at=t,acquisition_batch_id="batch.test")
    b=build_ola_canonical_observation_from_websocket(raw,received_at=t,acquisition_batch_id="batch.test")
    return a.observation_id==b.observation_id and a.source_id==SOURCE_ID
