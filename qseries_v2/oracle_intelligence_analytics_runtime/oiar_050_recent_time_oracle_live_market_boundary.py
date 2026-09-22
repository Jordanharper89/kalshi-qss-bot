
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash

OIAR_050_BUILD_ID="OIAR-050"
OIAR_050_REVISION="OIAR_050_RECENT_TIME_ORACLE_LIVE_MARKET_BOUNDARY_V1"
STAGE="oracle_live_recent_time_market_universe"
REQUIRED_INDEX="idx_oracle_canonical_observations_observed"
EXECUTION_AUTHORITY=False

def verify_required_index(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("""
                SELECT i.indisvalid,i.indisready,i.indislive,pg_get_indexdef(i.indexrelid)
                FROM pg_index i
                JOIN pg_class x ON x.oid=i.indexrelid
                JOIN pg_namespace n ON n.oid=x.relnamespace
                WHERE n.nspname='public' AND x.relname=%s
            """,(REQUIRED_INDEX,))
            row=cur.fetchone()
        c.rollback()
    if not row:
        raise RuntimeError("OIAR-050 required proven observed_at index missing")
    valid,ready,live,indexdef=row
    if not (valid and ready and live):
        raise RuntimeError("OIAR-050 required observed_at index is not healthy")
    normalized=" ".join(str(indexdef).lower().split())
    if "(observed_at, sequence_number)" not in normalized:
        raise RuntimeError("OIAR-050 observed_at index definition changed")
    return {"valid":True,"ready":True,"live":True,"indexdef":str(indexdef)}

def _payload(obj):
    if not isinstance(obj,dict): return {}
    raw=obj.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):
        return raw["payload"]
    p=obj.get("payload")
    return p if isinstance(p,dict) else {}

def _message(payload):
    m=payload.get("message")
    return m if isinstance(m,dict) else payload

def _ticker(payload):
    msg=_message(payload)
    return str(
        payload.get("source_market_id")
        or msg.get("market_ticker")
        or msg.get("ticker")
        or ""
    ).strip().upper()

def explain_recent_query(root=None,window_minutes=30,row_limit=100000):
    root=Path(root or Path.cwd()).resolve()
    cutoff=datetime.now(timezone.utc)-timedelta(minutes=max(1,int(window_minutes)))
    limit=max(1000,min(int(row_limit),250000))
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("""
                EXPLAIN (COSTS TRUE,FORMAT TEXT)
                SELECT sequence_number,observation_type,observed_at,canonical_observation_json
                FROM public.oracle_canonical_observations
                WHERE observed_at >= %s
                  AND observation_type IN ('ticker','trade')
                ORDER BY observed_at DESC,sequence_number DESC
                LIMIT %s
            """,(cutoff,limit))
            plan="\n".join(x[0] for x in cur.fetchall())
        c.rollback()
    return plan

def read_recent_oracle_live_markets(root=None,window_minutes=30,row_limit=100000,statement_timeout_ms=10000):
    root=Path(root or Path.cwd()).resolve()
    verify_required_index(root)
    cutoff=datetime.now(timezone.utc)-timedelta(minutes=max(1,int(window_minutes)))
    limit=max(1000,min(int(row_limit),250000))
    timeout=max(1000,min(int(statement_timeout_ms),30000))

    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SET LOCAL statement_timeout='{timeout}ms'")
            cur.execute("""
                SELECT sequence_number,observation_type,observed_at,canonical_observation_json
                FROM public.oracle_canonical_observations
                WHERE observed_at >= %s
                  AND observation_type IN ('ticker','trade')
                ORDER BY observed_at DESC,sequence_number DESC
                LIMIT %s
            """,(cutoff,limit))
            rows=cur.fetchall() or []
        c.rollback()

    by={}
    for seq,typ,observed,obj in rows:
        p=_payload(obj); ticker=_ticker(p)
        if not ticker: continue
        obs=observed.astimezone(timezone.utc)
        age=max(0.0,(datetime.now(timezone.utc)-obs).total_seconds())
        rec=by.setdefault(ticker,{
            "market_ticker":ticker,
            "latest_sequence":0,
            "latest_observed_at":"",
            "freshness_seconds":age,
            "ticker_observations":0,
            "trade_observations":0,
            "latest_payload":{},
        })
        if typ=="ticker": rec["ticker_observations"]+=1
        elif typ=="trade": rec["trade_observations"]+=1
        if int(seq)>int(rec["latest_sequence"]):
            rec["latest_sequence"]=int(seq)
            rec["latest_observed_at"]=obs.isoformat()
            rec["freshness_seconds"]=age
            rec["latest_payload"]=p

    markets=tuple(sorted(by.values(),key=lambda x:(x["freshness_seconds"],-x["latest_sequence"],x["market_ticker"])))
    if not markets:
        raise RuntimeError("OIAR-050 found no Oracle Live ticker/trade markets in recent-time window")
    return markets,len(rows),cutoff

def materialize_recent_time_market_universe(root=None):
    root=Path(root or Path.cwd()).resolve()
    markets,source_rows,cutoff=read_recent_oracle_live_markets(root)
    payload={
        "schema_version":"OIAR-050",
        "stage":STAGE,
        "cutoff_utc":cutoff.isoformat(),
        "source_rows":source_rows,
        "market_count":len(markets),
        "markets":list(markets),
        "source_index":REQUIRED_INDEX,
        "read_only_source":True,
        "execution_authority":False,
    }
    h=stable_hash(payload); sid="oiar-050-"+h[:32]
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute(f"""
                INSERT INTO public.{SNAPSHOT_TABLE}
                (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,
                 market_count,payload_json,payload_hash,read_only_source,execution_authority)
                VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE)
                ON CONFLICT(snapshot_id) DO NOTHING
            """,(sid,STAGE,"OIAR-050",OIAR_050_BUILD_ID,len(markets),
                 json.dumps(payload,sort_keys=True,default=str),h))
        c.commit()
    return sid,payload

def physical_probe(root=None):
    plan=explain_recent_query(root)
    sid,p=materialize_recent_time_market_universe(root)
    return {
        "snapshot_id":sid,
        "source_rows":p["source_rows"],
        "observed_markets":p["market_count"],
        "ticker_markets":sum(x["ticker_observations"]>0 for x in p["markets"]),
        "trade_markets":sum(x["trade_observations"]>0 for x in p["markets"]),
        "source_index":p["source_index"],
        "plan":plan,
        "execution_authority":False,
    }
