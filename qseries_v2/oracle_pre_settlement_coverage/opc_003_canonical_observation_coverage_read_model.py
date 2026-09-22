from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime,timezone
import json,os

OPC_003_BUILD_ID="OPC-003"
OPC_003_REVISION="OPC_003_CANONICAL_COVERAGE_FRESHNESS_READ_MODEL_RECERTIFIED"

@dataclass(frozen=True)
class CanonicalCoverageResult:
    sampled_markets:int; markets_with_canonical_observation:int; markets_without_canonical_observation:int
    coverage_rate:float; observed_tickers:tuple; missing_tickers:tuple; read_only:bool=True

def _db(root):
    url=os.environ.get("ORACLE_POSTGRESQL_URL") or os.environ.get("ORACLE_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:return url
    p=Path(root)/".env"
    if p.is_file():
        for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
            if "=" not in raw or raw.lstrip().startswith("#"):continue
            k,v=raw.split("=",1)
            if k.strip() in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL") and v.strip():
                return v.strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL / ORACLE_DATABASE_URL not configured")

def _ticker(obj):
    if isinstance(obj,list):
        for v in obj:
            x=_ticker(v)
            if x:return x
        return ""
    if not isinstance(obj,dict):return ""
    payload=obj.get("payload")
    if isinstance(payload,dict):
        for k in ("source_market_id","source_symbol","ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol"):
            v=payload.get(k)
            if isinstance(v,str) and v:return v
    for k in ("source_market_id","source_symbol","ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol"):
        v=obj.get(k)
        if isinstance(v,str) and v:return v
    return ""

def read_recent_canonical_market_freshness(root=None,lookback_hours=24,row_limit=250000):
    root=Path(root or Path.cwd()).resolve(); import psycopg
    conn=psycopg.connect(_db(root))
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT canonical_observation_json, observed_at
              FROM public.oracle_canonical_observations
              WHERE observed_at >= NOW()-(%s*INTERVAL '1 hour')
              ORDER BY observed_at DESC LIMIT %s""",(float(lookback_hours),int(row_limit)))
            rows=cur.fetchall()
    finally:conn.close()
    found={}
    for raw,observed in rows:
        obj=raw
        if isinstance(raw,str):
            try:obj=json.loads(raw)
            except Exception:continue
        if not isinstance(obj,dict) or str(obj.get("observation_type") or "")!="market_snapshot":continue
        t=_ticker(obj)
        if t and t not in found:
            if isinstance(observed,datetime):
                found[t]=observed if observed.tzinfo else observed.replace(tzinfo=timezone.utc)
            else:
                found[t]=datetime.fromisoformat(str(observed).replace("Z","+00:00"))
    return found

def read_recent_canonical_tickers(root=None,lookback_hours=24,row_limit=250000):
    return set(read_recent_canonical_market_freshness(root,lookback_hours,row_limit))

def evaluate_canonical_coverage(sample_tickers,canonical_tickers):
    sample=tuple(dict.fromkeys(str(v) for v in sample_tickers if str(v))); canonical={str(v) for v in canonical_tickers}
    observed=tuple(sorted(t for t in sample if t in canonical)); missing=tuple(sorted(t for t in sample if t not in canonical))
    return CanonicalCoverageResult(len(sample),len(observed),len(missing),len(observed)/len(sample) if sample else 0.0,observed,missing,True)

def verify_opc_003_canonical_observation_coverage_read_model():
    doc={"observation_type":"market_snapshot","payload":{"source_market_id":"KXTEST"}}
    x=evaluate_canonical_coverage(("KXTEST","KXMISSING"),{"KXTEST"})
    return _ticker(doc)=="KXTEST" and x.coverage_rate==0.5 and x.read_only
