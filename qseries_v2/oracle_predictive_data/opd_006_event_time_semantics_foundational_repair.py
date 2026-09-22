
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
SCAN=250000
INNER=(
 "payload.message.ts","payload.message.ts_ms","payload.message.time",
 "payload.observation_payload.anchor_epoch","payload.observation_payload.anchor_time",
 "payload.observation_payload.observed_at","payload.evidence_observed_at",
 "payload.snapshot_at","payload.event_time","payload.timestamp",
)
def get(o,p):
    c=o
    for x in p.split("."):
        if not isinstance(c,dict) or x not in c:return None
        c=c[x]
    return c
def epoch(v,p):
    if v is None:return None
    try:
        if p.endswith("ts_ms"):return float(v)/1000
        if p.endswith(".ts") or p.endswith("anchor_epoch"):return float(v)
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except:return None
def H(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd())
    with connect(root,autocommit=False) as c:
      with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='30000ms'")
        q.execute("SELECT max(sequence_number) FROM public.oracle_canonical_observations");hi=int(q.fetchone()[0] or 0);lo=max(1,hi-SCAN+1)
        q.execute("SELECT observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE sequence_number BETWEEN %s AND %s",(lo,hi));rows=q.fetchall() or []
      c.rollback()
    g=defaultdict(lambda:{"n":0,"paths":Counter(),"lags":defaultdict(list)})
    for outer,sid,typ,obj in rows:
      z=g[(str(sid),str(typ))];z["n"]+=1
      for p in INNER:
        e=epoch(get(obj,p),p)
        if e is not None:z["paths"][p]+=1;z["lags"][p].append(outer.timestamp()-e)
    out=[]
    for (sid,typ),z in g.items():
      ranked=sorted(z["paths"].items(),key=lambda x:(-x[1],INNER.index(x[0])))
      selected=ranked[0][0] if ranked else "OUTER_OBSERVED_AT_FALLBACK"
      lag=z["lags"].get(selected,[])
      out.append({"source_id":sid,"observation_type":typ,"rows":z["n"],
       "inner_candidates":[{"path":p,"rows":n} for p,n in ranked],
       "selected_event_time_path":selected,
       "time_semantics":"SOURCE_EVENT_TIME" if ranked else "ORACLE_OBSERVATION_TIME_FALLBACK",
       "median_outer_minus_event_seconds":sorted(lag)[len(lag)//2] if lag else None,
       "max_abs_outer_minus_event_seconds":max((abs(x) for x in lag),default=None)})
    out.sort(key=lambda x:(-x["rows"],x["source_id"],x["observation_type"]))
    s={"schema_version":"OPD-006","replaces_event_time_semantics_of":"OPD-003","sequence_window":[lo,hi],
       "groups":out,"source_time_groups":sum(x["time_semantics"]=="SOURCE_EVENT_TIME" for x in out),
       "fallback_groups":sum(x["time_semantics"]!="SOURCE_EVENT_TIME" for x in out),"hash":H(out),
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"predictive_data"/"opd_006_event_time_semantics_repair.json";p.write_text(json.dumps(s,indent=2,sort_keys=True,default=str))
    return s,p
