from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable
import hashlib, json, math

READ_ONLY = True
EXECUTION_AUTHORITY = False

def _iso(v):
    if v is None: return None
    if isinstance(v, datetime):
        if v.tzinfo is None: v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).isoformat()
    return str(v)

def _f(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def _dig(o, *paths):
    for path in paths:
        cur=o
        ok=True
        for k in path.split("."):
            if isinstance(cur, dict) and k in cur: cur=cur[k]
            else: ok=False; break
        if ok and cur is not None: return cur
    return None

AUDIT_SCHEMA="SSI-001"
PRICE_KEYS=("price","price_usd","usd_price","token_price","close","mid","value")
LIQ_KEYS=("liquidity","liquidity_usd","tvl","tvl_usd","reserve_usd")
TIME_KEYS=("observed_at","timestamp","block_time","blockTime","time")
ASSET_KEYS=("mint","token_mint","base_mint","asset","symbol","pool","pool_address")
def audit_rows(rows: Iterable[dict[str,Any]]) -> dict[str,Any]:
    rows=list(rows); assets=set(); sources=set(); types=set(); times=[]; priced=liquid=0
    for r in rows:
        a=_dig(r,*ASSET_KEYS); s=_dig(r,"source_id","provider"); t=_dig(r,"observation_type","type")
        if a: assets.add(str(a))
        if s: sources.add(str(s))
        if t: types.add(str(t))
        if any(_f(_dig(r,k)) is not None for k in PRICE_KEYS): priced+=1
        if any(_f(_dig(r,k)) is not None for k in LIQ_KEYS): liquid+=1
        tv=_dig(r,*TIME_KEYS)
        if tv is not None: times.append(str(tv))
    return {"schema_version":AUDIT_SCHEMA,"rows":len(rows),"assets":len(assets),
            "sources":tuple(sorted(sources)),"observation_types":tuple(sorted(types)),
            "priced_rows":priced,"liquidity_rows":liquid,
            "first_observed_at":min(times) if times else None,
            "last_observed_at":max(times) if times else None,
            "profitability_input_ready": bool(rows and priced>=2),
            "read_only":True,"execution_authority":False}
def audit_jsonl(path):
    rows=[]
    with open(path,encoding="utf-8") as f:
        for line in f:
            try: rows.append(json.loads(line))
            except Exception: pass
    return audit_rows(rows)
