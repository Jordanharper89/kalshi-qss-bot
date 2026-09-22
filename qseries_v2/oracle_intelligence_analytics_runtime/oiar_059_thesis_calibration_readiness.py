from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_058_deterministic_market_thesis_signature import read_latest_deterministic_market_thesis_signatures

OIAR_059_BUILD_ID="OIAR-059"
STAGE="thesis_calibration_readiness"

MIN_OUTCOMES_FOR_EMPIRICAL_RATE=30

def _historical_support(root, signature):
    # Read only from prior OIAR-059 snapshots if/when actual outcome-calibrated
    # support is written by a future certified learning bridge. This build
    # intentionally does not infer outcomes from prices.
    return {"settled_outcomes":0,"correct_outcomes":0,"empirical_rate":None}

def materialize_thesis_calibration_readiness(root=None):
    root=Path(root or Path.cwd()).resolve()
    src=read_latest_deterministic_market_thesis_signatures(root)
    if not src:raise RuntimeError("OIAR-059 requires OIAR-058")
    rows=[]
    for r in src.get("markets",[]):
        support=_historical_support(root,r["thesis_signature"])
        n=support["settled_outcomes"]
        status="CALIBRATED" if n>=MIN_OUTCOMES_FOR_EMPIRICAL_RATE else "INSUFFICIENT_OUTCOMES"
        rows.append({**r,"calibration_status":status,"settled_outcomes":n,
                     "correct_outcomes":support["correct_outcomes"],"empirical_rate":support["empirical_rate"],
                     "minimum_outcomes_required":MIN_OUTCOMES_FOR_EMPIRICAL_RATE})
    body={"schema_version":"OIAR-059","stage":STAGE,"market_count":len(rows),"markets":rows,
          "calibrated_count":sum(v["calibration_status"]=="CALIBRATED" for v in rows),
          "no_price_proxy_for_outcomes":True,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-059-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}
        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,"OIAR-059",OIAR_059_BUILD_ID,datetime.now(timezone.utc),len(rows),
         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
    return body

def read_latest_thesis_calibration_readiness(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
        r=q.fetchone();c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-059 snapshot hash mismatch")
    return p

def physical_probe(root=None):
    x=materialize_thesis_calibration_readiness(root)
    return {"theses":x["market_count"],"calibrated_count":x["calibrated_count"],"execution_authority":False}
