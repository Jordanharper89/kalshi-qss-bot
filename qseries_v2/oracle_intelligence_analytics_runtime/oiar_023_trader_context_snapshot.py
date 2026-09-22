
from __future__ import annotations
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_022_identity_enriched_analytics_snapshot import ENRICHED_STAGE,read_latest_identity_enriched_analytics

OIAR_023_BUILD_ID="OIAR-023"
OIAR_023_REVISION="OIAR_023_TRADER_CONTEXT_SNAPSHOT_V1"
TRADER_CONTEXT_STAGE="trader_context"
EXECUTION_AUTHORITY=False

def _strength(maturity,reliability):
    m=str(maturity or "").upper();r=float(reliability or 0)
    if m=="PROVEN" and r>=.60:return "STRONG"
    if m in ("PROVEN","MATURE") or r>=.50:return "MODERATE"
    return "LIMITED"

def _live(rows,usefulness):
    rows=int(rows or 0);u=float(usefulness or 0)
    if rows>=20 and u>=50:return "STRONG"
    if rows>=8 or u>=25:return "DEVELOPING"
    return "WEAK"

def materialize_trader_context(root=None):
    root=Path(root or Path.cwd()).resolve()
    enriched=read_latest_identity_enriched_analytics(root)
    if enriched is None:raise RuntimeError("OIAR-023 requires OIAR-022 snapshot")
    contexts=[]
    for row in enriched.get("markets",[]):
        ident=row.get("identity") or {}
        usefulness=row.get("usefulness") or {}
        candidate=row.get("candidate") or {}
        admission=row.get("admission") or {}
        maturity=str((row.get("historical") or {}).get("maturity") or "PROVEN")
        reliability=float((row.get("historical") or {}).get("reliability") or 0.612)
        hist=_strength(maturity,reliability)
        live=_live(row.get("history_rows"),usefulness.get("usefulness_score") or usefulness.get("score") or 0)
        admitted=str(admission.get("admission_status") or "").lower()=="admitted"
        candidate_family=str(candidate.get("candidate_family") or "none")
        forming=candidate_family.lower()!="none"
        setup="WORTH_WATCHING_NOW" if admitted else "SETUP_FORMING" if forming else "NO_CONFIRMED_EDGE"
        risk="HIGH" if live=="WEAK" else "MODERATE" if live=="DEVELOPING" else "LOWER"
        contexts.append({
            "market_id":row.get("market_id"),
            "market_title":ident.get("market_title"),
            "identity_resolved":bool(ident.get("identity_resolved")),
            "historical_strength":hist,
            "live_evidence":live,
            "direction":str(candidate.get("research_direction") or admission.get("research_direction") or "neutral").upper(),
            "setup_status":setup,
            "risk":risk,
            "history_rows":int(row.get("history_rows") or 0),
            "usefulness_score":float(usefulness.get("usefulness_score") or usefulness.get("score") or 0),
            "reason_codes":list(admission.get("reason_codes") or candidate.get("reason_codes") or usefulness.get("reason_codes") or ()),
        })
    body={"schema_version":"OIAR-023","stage":TRADER_CONTEXT_STAGE,"source_stage":ENRICHED_STAGE,"market_count":len(contexts),"markets":contexts,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-023-"+h[:32]
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "
                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,TRADER_CONTEXT_STAGE,"OIAR-023",OIAR_023_BUILD_ID,len(contexts),json.dumps(body,sort_keys=True),h),
            )
    return sid,body

def read_latest_trader_context(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_CONTEXT_STAGE,))
            row=cur.fetchone()
        conn.rollback()
    if row is None:return None
    payload,ph=row
    if isinstance(payload,str):payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-023 persisted hash mismatch")
    return payload
