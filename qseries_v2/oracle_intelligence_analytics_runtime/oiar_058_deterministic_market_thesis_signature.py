from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_057_current_market_evidence_vector import read_latest_current_market_evidence_vectors

OIAR_058_BUILD_ID="OIAR-058"
STAGE="deterministic_market_thesis_signature"

def _signature(row):
    e=row["evidence"]
    factors=tuple(sorted(set(e.get("positive_factors",[])+e.get("negative_factors",[]))))
    direction=str(row.get("direction","neutral")).lower()
    raw="|".join((direction,)+factors)
    return sha256(raw.encode()).hexdigest(), factors

def materialize_deterministic_market_thesis_signatures(root=None):
    root=Path(root or Path.cwd()).resolve()
    src=read_latest_current_market_evidence_vectors(root)
    if not src:raise RuntimeError("OIAR-058 requires OIAR-057")
    rows=[]
    for r in src.get("markets",[]):
        sig,factors=_signature(r)
        rows.append({"market_id":r["market_id"],"rank":r["rank"],"title":r.get("title",""),
                     "research_score":r.get("research_score","0"),"direction":r.get("direction","neutral"),
                     "thesis_signature":sig,"factors":list(factors),
                     "thesis_statement":" + ".join(factors) if factors else "insufficient structured factors",
                     "probability":None,"calibration_status":"UNVERIFIED"})
    body={"schema_version":"OIAR-058","stage":STAGE,"market_count":len(rows),"markets":rows,
          "probabilities_forbidden_without_outcome_calibration":True,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-058-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}
        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,"OIAR-058",OIAR_058_BUILD_ID,datetime.now(timezone.utc),len(rows),
         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
    return body

def read_latest_deterministic_market_thesis_signatures(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
        r=q.fetchone();c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-058 snapshot hash mismatch")
    return p

def physical_probe(root=None):
    x=materialize_deterministic_market_thesis_signatures(root)
    return {"theses":x["market_count"],"probabilities_populated":sum(v["probability"] is not None for v in x["markets"]),"execution_authority":False}
