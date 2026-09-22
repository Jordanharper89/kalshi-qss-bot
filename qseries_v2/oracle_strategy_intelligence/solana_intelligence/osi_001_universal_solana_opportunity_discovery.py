from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Iterable

EXECUTION_AUTHORITY = False
READ_ONLY = True

EVENT_TYPES = {
    "NEW_POOL", "LIQUIDITY_ADDED", "LIQUIDITY_REMOVED", "FREEZE_AUTHORITY",
    "MINT_AUTHORITY", "SWAP_ACCELERATION", "WALLET_CLUSTER", "HOLDER_CONCENTRATION",
    "POOL_DEPTH_CHANGE", "VOLUME_BURST", "PRICE_ACCELERATION", "RUG_RISK_CHANGE",
}

def _dt(v: str) -> datetime:
    d = datetime.fromisoformat(v.replace("Z","+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def _id(x: dict) -> str:
    raw = json.dumps(x, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def discover(events: Iterable[dict], now_iso: str, max_age_seconds: int = 300) -> list[dict]:
    now = _dt(now_iso)
    out = []
    for e in events:
        typ, asset, ts = e.get("event_type"), e.get("asset_key"), e.get("observed_at")
        if typ not in EVENT_TYPES or not asset or not ts:
            continue
        t = _dt(ts)
        age = (now-t).total_seconds()
        if age < 0 or age > max_age_seconds:
            continue
        row = {
            "asset_key": str(asset),
            "event_type": str(typ),
            "observed_at": t.isoformat(),
            "source": str(e.get("source") or "unknown"),
            "source_record_id": str(e.get("source_record_id") or ""),
            "features": dict(e.get("features") or {}),
            "read_only": True,
            "execution_authority": False,
        }
        row["opportunity_seed_id"] = _id({
            "asset_key": row["asset_key"],
            "event_type": row["event_type"],
            "observed_at": row["observed_at"],
            "source": row["source"],
            "source_record_id": row["source_record_id"],
        })
        out.append(row)
    out.sort(key=lambda x:(x["observed_at"],x["asset_key"],x["event_type"],x["opportunity_seed_id"]))
    return out
