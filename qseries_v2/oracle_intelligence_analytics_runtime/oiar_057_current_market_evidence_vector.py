from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
from collections import Counter

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics
from .oiar_056_current_market_research_ranking import read_latest_current_market_research_ranking

OIAR_057_BUILD_ID="OIAR-057"
STAGE="current_market_evidence_vector"

def _vector(m):
    f=m.get("features",{}); u=m.get("usefulness",{}); a=m.get("admission",{}); c=m.get("candidate",{})
    positive=[]; negative=[]
    if float(u.get("usefulness_score",0) or 0)>=20: positive.append("usefulness")
    if float(f.get("latest_volume_fp",0) or 0)>=1000: positive.append("volume")
    if float(f.get("absolute_movement_dollars",0) or 0)>0: positive.append("movement")
    if str(c.get("research_direction","neutral")).lower()!="neutral": positive.append("directional_signal")
    negative.extend(str(x) for x in u.get("reason_codes",[]) or [])
    negative.extend(str(x) for x in a.get("reason_codes",[]) or [])
    return {"positive_factors":sorted(set(positive)),"negative_factors":sorted(set(negative)),
            "observation_count":f.get("observation_count",0),"latest_price_dollars":f.get("latest_price_dollars"),
            "latest_volume_fp":f.get("latest_volume_fp"),"spread_to_price_ratio":f.get("spread_to_price_ratio"),
            "directional_change_ratio":f.get("directional_change_ratio"),"normalized_volatility_ratio":f.get("normalized_volatility_ratio")}

def materialize_current_market_evidence_vectors(root=None):
    root=Path(root or Path.cwd()).resolve()
    analytics=read_latest_current_trader_analytics(root); ranking=read_latest_current_market_research_ranking(root)
    if not analytics or not ranking:raise RuntimeError("OIAR-057 requires OIAR-054 and OIAR-056")
    by={m["market_id"]:m for m in analytics.get("markets",[])}
    rows=[]; counts=Counter()
    for r in ranking.get("markets",[]):
        mid=r["market_id"]; m=by.get(mid)
        if not m:continue
        v=_vector(m)
        for reason in v["negative_factors"]: counts[reason]+=1
        rows.append({"market_id":mid,"rank":r["rank"],"title":r.get("title",""),"research_score":r["research_score"],
                     "direction":r.get("direction","neutral"),"evidence":v})
    body={"schema_version":"OIAR-057","stage":STAGE,"market_count":len(rows),"markets":rows,
          "negative_factor_counts":dict(sorted(counts.items())),"evidence_is_descriptive_not_predictive":True,
          "read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-057-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}
        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,"OIAR-057",OIAR_057_BUILD_ID,datetime.now(timezone.utc),len(rows),
        json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
    return body

def read_latest_current_market_evidence_vectors(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
        r=q.fetchone();c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-057 snapshot hash mismatch")
    return p

def physical_probe(root=None):
    x=materialize_current_market_evidence_vectors(root)
    return {"evidence_markets":x["market_count"],"negative_factor_types":len(x["negative_factor_counts"]),"execution_authority":False}
