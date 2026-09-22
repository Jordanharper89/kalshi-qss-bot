from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, InvalidOperation
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics

OIAR_056_BUILD_ID="OIAR-056"
STAGE="current_market_research_ranking"

def _num(v):
    try: return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError): return Decimal("0")

def _research_score(m):
    usefulness=_num(m.get("usefulness",{}).get("usefulness_score"))
    admission=_num(m.get("admission",{}).get("admission_score"))
    volume=_num(m.get("features",{}).get("latest_volume_fp"))
    obs=_num(m.get("features",{}).get("observation_count"))
    movement=_num(m.get("features",{}).get("absolute_movement_dollars"))
    # Ranking is research priority, not trade authorization.
    return usefulness + admission + min(volume/Decimal("1000"), Decimal("20")) + min(obs/Decimal("10"), Decimal("10")) + movement*Decimal("100")

def materialize_current_market_research_ranking(root=None, limit=100):
    root=Path(root or Path.cwd()).resolve()
    src=read_latest_current_trader_analytics(root)
    if not src: raise RuntimeError("OIAR-056 requires certified OIAR-054 analytics snapshot")
    ranked=[]
    for m in src.get("markets",[]):
        item={
            "market_id":m.get("market_id"),
            "title":m.get("market",{}).get("title",""),
            "status":m.get("market",{}).get("status",""),
            "event_ticker":m.get("market",{}).get("event_ticker",""),
            "research_score":str(_research_score(m).quantize(Decimal("0.01"))),
            "admission_status":m.get("admission",{}).get("admission_status","unknown"),
            "admission_score":m.get("admission",{}).get("admission_score","0"),
            "usefulness_classification":m.get("usefulness",{}).get("classification","unknown"),
            "usefulness_score":m.get("usefulness",{}).get("usefulness_score","0"),
            "direction":m.get("candidate",{}).get("research_direction","neutral"),
            "history_rows":m.get("history_rows",0),
            "reason_codes":m.get("usefulness",{}).get("reason_codes",[]),
        }
        ranked.append(item)
    ranked.sort(key=lambda x:(-_num(x["research_score"]), str(x["market_id"])))
    ranked=ranked[:max(1,int(limit))]
    for i,x in enumerate(ranked,1): x["rank"]=i
    body={"schema_version":"OIAR-056","stage":STAGE,"market_count":len(ranked),"markets":ranked,
          "ranking_is_research_priority_only":True,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body); sid="oiar-056-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor()
        q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}
        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,"OIAR-056",OIAR_056_BUILD_ID,datetime.now(timezone.utc),len(ranked),
         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h))
        c.commit()
    return body

def read_latest_current_market_research_ranking(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor(); q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
        r=q.fetchone(); c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-056 snapshot hash mismatch")
    return p

def physical_probe(root=None):
    x=materialize_current_market_research_ranking(root)
    return {"ranked_markets":x["market_count"],"top_market":x["markets"][0]["market_id"],"execution_authority":False}
