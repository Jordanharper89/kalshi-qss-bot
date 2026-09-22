from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import load_historical_experience_read_model
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, STATE_TABLE, ensure_analytics_snapshot_schema, stable_hash

OIAR_002_BUILD_ID="OIAR-002"
STAGE="reasoning_market_cohort"

@dataclass(frozen=True)
class ReasoningMarketCohortSnapshot:
    snapshot_id:str
    market_count:int
    learner_state_hash:str
    lineage_current:bool
    payload_hash:str
    generated_at:str
    read_only:bool=True
    execution_authority:bool=False

def build_reasoning_market_cohort_payload(root=None):
    root=Path(root or Path.cwd()).resolve()
    model=load_historical_experience_read_model(root)
    seen=set(); markets=[]
    for c in model.contexts:
        t=str(c.market_ticker or "").strip().upper()
        if not t or t in seen: continue
        seen.add(t)
        markets.append({
            "market_ticker":t,
            "series_key":str(c.series_key or ""),
            "maturity":str(c.maturity or ""),
            "series_admitted":bool(c.series_admitted),
            "experience_available":bool(c.experience_available),
            "regime_id":str(c.regime_id or ""),
            "reliability":float(c.reliability or 0.0),
            "learner_state_hash":str(c.learner_state_hash or ""),
            "reason":str(c.reason or ""),
        })
    markets.sort(key=lambda x:x["market_ticker"])
    return {
        "schema_version":"OIAR-002",
        "stage":STAGE,
        "learner_state_hash":str(model.learner_state_hash or ""),
        "attestation_state_hash":str(model.attestation_state_hash or ""),
        "lineage_current":bool(model.lineage_current),
        "markets_reasoned":int(model.markets_reasoned),
        "experience_contexts":int(model.experience_contexts),
        "withheld_contexts":int(model.withheld_contexts),
        "blind_contexts":int(model.blind_contexts),
        "market_count":len(markets),
        "markets":markets,
        "read_only_source":True,
        "execution_authority":False,
    }

def materialize_current_reasoning_market_cohort(root=None,generated_at=None):
    root=Path(root or Path.cwd()).resolve()
    ensure_analytics_snapshot_schema(root)
    payload=build_reasoning_market_cohort_payload(root)
    if not payload["lineage_current"]: raise RuntimeError("OIAR-002 refuses stale lineage")
    if payload["market_count"]<=0: raise RuntimeError("OIAR-002 cohort is empty")
    generated=generated_at or datetime.now(timezone.utc)
    if generated.tzinfo is None: raise ValueError("generated_at must be timezone-aware")
    ph=stable_hash(payload); sid=f"oiar-002-{ph[:32]}"
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,STAGE,"OIAR-002",OIAR_002_BUILD_ID,generated,payload["market_count"],json.dumps(payload,sort_keys=True,separators=(",",":")),ph)
            )
            cur.execute(
                f"UPDATE public.{STATE_TABLE} SET last_successful_snapshot_id=%s,last_successful_stage=%s,last_successful_at=%s,last_completed_at=%s,status='IDLE',last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",
                (sid,STAGE,generated,generated)
            )
        conn.commit()
    return ReasoningMarketCohortSnapshot(sid,payload["market_count"],payload["learner_state_hash"],True,ph,generated.astimezone(timezone.utc).isoformat(),True,False)

def read_latest_reasoning_market_cohort(root=None):
    root=Path(root or Path.cwd()).resolve(); ensure_analytics_snapshot_schema(root)
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT snapshot_id,market_count,payload_json,payload_hash,generated_at FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
            row=cur.fetchone()
        conn.rollback()
    if row is None: return None
    sid,count,payload,ph,generated=row
    if isinstance(payload,str): payload=json.loads(payload)
    if stable_hash(payload)!=str(ph): raise RuntimeError("OIAR-002 payload hash mismatch")
    return ReasoningMarketCohortSnapshot(str(sid),int(count),str(payload.get("learner_state_hash") or ""),bool(payload.get("lineage_current")),str(ph),generated.astimezone(timezone.utc).isoformat(),True,False)

def verify_oiar_002_current_reasoning_market_cohort(root=None):
    x=read_latest_reasoning_market_cohort(root)
    return bool(x and x.market_count>0 and x.lineage_current and x.read_only and not x.execution_authority)
