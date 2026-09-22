from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)

OPC_006_BUILD_ID="OPC-006"
OPC_006_REVISION="OPC_006_UNIVERSAL_MARKET_SNAPSHOT_CANONICALIZER_CORRECTION_V3"

def _utc(value=None):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

def _stable(value):
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",",":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

def _money(row,key,dollar_key=None):
    if dollar_key and row.get(dollar_key) not in (None,""):
        return str(row[dollar_key])
    value=row.get(key)
    if value in (None,""):
        return "0.0000"
    try:
        return f"{float(value)/100.0:.4f}"
    except Exception:
        return str(value)

def _fp(row,*keys):
    for key in keys:
        value=row.get(key)
        if value not in (None,""):
            return str(value)
    return "0.00"

def _epoch_token(acquired):
    # Microsecond precision guarantees that a later observation of unchanged
    # market state gets a distinct source observation identity.
    return acquired.strftime("%Y%m%dT%H%M%S%fZ")

def build_universal_market_snapshot(
    market,
    *,
    acquired_at=None,
    batch_id=None,
):
    if not isinstance(market,dict):
        raise TypeError("market must be dict")

    ticker=str(market.get("ticker") or "").strip()
    if not ticker:
        raise ValueError("market ticker required")

    acquired=_utc(acquired_at)
    observed=_utc(
        market.get("updated_time")
        or market.get("last_updated_time")
        or acquired
    )

    # Stable state identity remains independent of observation time.
    state_hash=_stable(market)

    # Observation identity represents "Oracle observed this state at this epoch".
    observation_epoch=_epoch_token(acquired)

    payload={
        "source_market_id":ticker,
        "source_symbol":ticker,
        "event_ticker":str(market.get("event_ticker") or ""),
        "market_title":str(
            market.get("title")
            or market.get("market_title")
            or ""
        ),
        "source_status_filter":str(market.get("status") or "open"),

        "yes_bid_dollars":_money(market,"yes_bid","yes_bid_dollars"),
        "yes_bid_size_fp":_fp(market,"yes_bid_size_fp","yes_bid_size"),
        "yes_ask_dollars":_money(market,"yes_ask","yes_ask_dollars"),
        "yes_ask_size_fp":_fp(market,"yes_ask_size_fp","yes_ask_size"),
        "no_bid_dollars":_money(market,"no_bid","no_bid_dollars"),
        "no_ask_dollars":_money(market,"no_ask","no_ask_dollars"),
        "last_price_dollars":_money(
            market,
            "last_price",
            "last_price_dollars",
        ),
        "volume_fp":_fp(market,"volume_fp","volume"),
        "volume_24h_fp":_fp(market,"volume_24h_fp","volume_24h"),
        "open_interest_fp":_fp(
            market,
            "open_interest_fp",
            "open_interest",
        ),
        "liquidity_dollars":str(
            market.get("liquidity_dollars")
            or market.get("liquidity")
            or "0.0000"
        ),

        "previous_yes_bid_dollars":"0.0000",
        "previous_yes_ask_dollars":"0.0000",
        "previous_price_dollars":"0.0000",

        "source_open_time":market.get("open_time"),
        "source_close_time":market.get("close_time"),
        "source_expiration_time":market.get("expiration_time"),

        "opc_snapshot":True,
        "opc_source_state_hash":state_hash,
        "opc_observation_epoch":observation_epoch,
        "execution_allowed":False,
    }

    raw=RawSourceObservation.create(
        source_observation_id=(
            "opc.kalshi.market."
            + ticker
            + "."
            + state_hash
            + "."
            + observation_epoch
        ),
        observed_at=observed,
        observation_type="market_snapshot",
        payload=payload,
        provenance={
            "source_id":"source.kalshi.market_data",
            "adapter_id":"adapter.oracle.kalshi.opc.universal_snapshot",
            "source_api":"kalshi_trade_api_v2",
            "source_endpoint":"/markets",
            "http_method":"GET",
            "public_endpoint":True,
            "shadow_mode":True,
            "opc_build":"OPC-006-CORRECTION-V3",
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=acquired,
        acquisition_batch_id=str(
            batch_id
            or (
                "batch.opc.snapshot."
                + observation_epoch
            )
        ),
    )

def verify_opc_006_universal_market_snapshot_canonicalizer():
    base={"ticker":"KXTEST","status":"open","yes_bid":31,"yes_ask":33}

    first=build_universal_market_snapshot(
        base,
        acquired_at="2026-08-16T20:00:00.000001Z",
        batch_id="batch.test.1",
    )
    second=build_universal_market_snapshot(
        base,
        acquired_at="2026-08-16T20:00:00.000002Z",
        batch_id="batch.test.2",
    )

    p1=dict(first.payload)
    p2=dict(second.payload)

    return (
        first.read_only is True
        and first.execution_allowed is False
        and first.observation_type=="market_snapshot"
        and p1.get("source_market_id")=="KXTEST"
        and p1.get("opc_source_state_hash")==p2.get("opc_source_state_hash")
        and p1.get("opc_observation_epoch")!=p2.get("opc_observation_epoch")
        and first.observation_id!=second.observation_id
        and first.content_hash!=second.content_hash
    )
