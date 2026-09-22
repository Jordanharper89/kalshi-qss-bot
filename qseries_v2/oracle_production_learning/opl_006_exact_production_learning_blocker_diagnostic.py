from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from collections import Counter
import json

from .opl_001_production_learning_foundation import connect
from .opl_002_canonical_evidence_index import INDEX_TABLE

OPL_006_BUILD_ID="OPL-006"
OPL_006_REVISION="OPL_006_EXACT_PRODUCTION_LEARNING_BLOCKER_DIAGNOSTIC_V1"

@dataclass(frozen=True)
class MarketTrace:
    ticker:str
    event_ticker:str
    series_ticker:str
    settlement_ts:str
    exact_index_rows:int
    exact_pre_settlement_rows:int
    exact_post_settlement_rows:int
    event_index_rows:int
    series_index_rows:int
    exact_min_observed_at:str
    exact_max_observed_at:str
    canonical_source_observation_rows:int
    canonical_json_text_rows:int
    failure_class:str

def _credentials(root):
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    return load_kalshi_credentials(root=root)

def _get(credentials,path,params,timeout=15):
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
    return kalshi_rest_get(credentials,path,params,timeout)

def _norm(v):
    return str(v or "").strip().upper()

def _settlement_ts(m):
    return str(
        m.get("settlement_ts")
        or m.get("settled_ts")
        or m.get("settled_time")
        or ""
    ).strip()

def fetch_real_settled_samples(root=None,limit=25):
    root=Path(root or Path.cwd()).resolve()
    c=_credentials(root)
    r=_get(c,"/markets",{"limit":max(1,min(int(limit),1000)),"status":"settled"},15)
    out=[]
    for raw in r.body.get("markets",()):
        ticker=_norm(raw.get("ticker"))
        ts=_settlement_ts(raw)
        if not ticker or not ts:
            continue
        out.append(dict(raw))
        if len(out)>=int(limit):
            break
    return tuple(out)

def _index_stats(cur,identity,settlement_ts):
    identity=_norm(identity)
    if not identity:
        return (0,0,0,"","")
    cur.execute(
        f"""SELECT
              COUNT(*),
              COUNT(*) FILTER (WHERE observed_at < %s),
              COUNT(*) FILTER (WHERE observed_at >= %s),
              COALESCE(MIN(observed_at),''),
              COALESCE(MAX(observed_at),'')
            FROM public.{INDEX_TABLE}
            WHERE ticker=%s""",
        (settlement_ts,settlement_ts,identity),
    )
    row=cur.fetchone()
    return int(row[0]),int(row[1]),int(row[2]),str(row[3] or ""),str(row[4] or "")

def _count_index(cur,identity):
    identity=_norm(identity)
    if not identity:
        return 0
    cur.execute(f"SELECT COUNT(*) FROM public.{INDEX_TABLE} WHERE ticker=%s",(identity,))
    return int(cur.fetchone()[0])

def _canonical_exact_counts(cur,ticker):
    # These are bounded exact checks against the two most likely identity surfaces.
    cur.execute(
        """SELECT COUNT(*)
           FROM public.oracle_canonical_observations
           WHERE UPPER(COALESCE(source_observation_id,''))=%s""",
        (_norm(ticker),),
    )
    source_rows=int(cur.fetchone()[0])

    # JSON text scan is intentionally used only for a small diagnostic sample.
    cur.execute(
        """SELECT COUNT(*)
           FROM public.oracle_canonical_observations
           WHERE canonical_observation_json::text ILIKE %s""",
        ("%"+str(ticker)+"%",),
    )
    json_rows=int(cur.fetchone()[0])
    return source_rows,json_rows

def classify_trace(exact_rows,pre_rows,post_rows,event_rows,series_rows,source_rows,json_rows):
    if exact_rows>0 and pre_rows>0:
        return "MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES"
    if exact_rows>0 and pre_rows==0 and post_rows>0:
        return "EVIDENCE_EXISTS_ONLY_AFTER_SETTLEMENT"
    if exact_rows==0 and (event_rows>0 or series_rows>0):
        return "IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES"
    if exact_rows==0 and json_rows>0:
        return "CANONICAL_CONTAINS_TICKER_BUT_EVIDENCE_INDEX_IDENTITY_IS_WRONG"
    if exact_rows==0 and source_rows>0:
        return "SOURCE_IDENTITY_EXISTS_BUT_EVIDENCE_INDEX_DID_NOT_CAPTURE_IT"
    return "NO_CANONICAL_PRESETTLEMENT_COVERAGE_FOR_SETTLED_TICKER"

def trace_market(root,market):
    ticker=_norm(market.get("ticker"))
    event_ticker=_norm(market.get("event_ticker"))
    series_ticker=_norm(market.get("series_ticker"))
    settlement_ts=_settlement_ts(market)

    with connect(root) as conn:
        with conn.cursor() as cur:
            exact_rows,pre_rows,post_rows,min_at,max_at=_index_stats(cur,ticker,settlement_ts)
            event_rows=_count_index(cur,event_ticker)
            series_rows=_count_index(cur,series_ticker)
            source_rows,json_rows=_canonical_exact_counts(cur,ticker)

    failure=classify_trace(
        exact_rows,pre_rows,post_rows,event_rows,series_rows,source_rows,json_rows
    )
    return MarketTrace(
        ticker,event_ticker,series_ticker,settlement_ts,
        exact_rows,pre_rows,post_rows,event_rows,series_rows,
        min_at,max_at,source_rows,json_rows,failure
    )

def run_exact_blocker_diagnostic(root=None,sample_size=10):
    root=Path(root or Path.cwd()).resolve()
    markets=fetch_real_settled_samples(root,max(1,int(sample_size)))
    traces=tuple(trace_market(root,m) for m in markets)
    classes=Counter(t.failure_class for t in traces)

    if not traces:
        overall="NO_SETTLED_SAMPLE_RETURNED"
    elif len(classes)==1:
        overall=next(iter(classes))
    else:
        overall="MIXED_FAILURE_CLASSES"

    return {
        "sample_size":len(traces),
        "overall_failure_class":overall,
        "failure_counts":dict(classes),
        "traces":[asdict(t) for t in traces],
        "execution_authority":False,
    }

def write_exact_blocker_report(root=None,sample_size=10):
    root=Path(root or Path.cwd()).resolve()
    report=run_exact_blocker_diagnostic(root,sample_size)
    path=root/"qseries_v2"/"oracle_production_learning"/"OPL_006_EXACT_BLOCKER_REPORT.json"
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,report

def verify_opl_006_exact_production_learning_blocker_diagnostic(root=None):
    return (
        OPL_006_BUILD_ID=="OPL-006"
        and classify_trace(1,1,0,0,0,0,0)=="MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES"
        and classify_trace(0,0,0,1,0,0,0)=="IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES"
    )
