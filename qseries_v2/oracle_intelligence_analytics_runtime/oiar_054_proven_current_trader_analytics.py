from __future__ import annotations
from dataclasses import asdict,is_dataclass
from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import OracleMarketStatisticsEngine
from qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureExtractionEngine
from qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import OracleMarketUsefulnessScoringEngine
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import OracleOpportunityCandidateGenerator
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_052_proven_current_canonical_trader_cohort import read_latest_current_trader_cohort
from .oiar_053_proven_current_market_history import read_latest_current_market_history

OIAR_054_BUILD_ID="OIAR-054"
STAGE="proven_current_trader_analytics"

def _d(x):
    if hasattr(x,"to_dict"): return dict(x.to_dict())
    if is_dataclass(x): return asdict(x)
    return dict(x.__dict__)

def _aware_datetime(value):
    if isinstance(value,datetime):
        dt=value
    elif isinstance(value,str):
        text=value.strip()
        if text.endswith("Z"):
            text=text[:-1]+"+00:00"
        dt=datetime.fromisoformat(text)
    else:
        raise TypeError("observed_at must be datetime or ISO-8601 string")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain timezone information")
    return dt.astimezone(timezone.utc)

def materialize_current_trader_analytics(root=None):
    root=Path(root or Path.cwd()).resolve()
    cohort=read_latest_current_trader_cohort(root)
    hist=read_latest_current_market_history(root)
    if not cohort or not hist:
        raise RuntimeError("OIAR-054 requires OIAR-052 and OIAR-053")

    meta={x["market_ticker"]:x for x in cohort["markets"]}
    group={x["market_ticker"]:x["history"] for x in hist["markets"]}
    cf=lambda:connect(root,autocommit=False)
    n=max(1,len(group))

    se=OracleMarketStatisticsEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)
    fe=OracleCanonicalMarketFeatureExtractionEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)
    ue=OracleMarketUsefulnessScoringEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)
    ce=OracleOpportunityCandidateGenerator(connection_factory=cf,market_limit=n,history_limit_per_market=250)
    ae=OracleOpportunityAdmissionGate(connection_factory=cf,market_limit=n,history_limit_per_market=250)

    records=[]
    for mid,rr in group.items():
        rows=[
            (
                mid,
                _aware_datetime(r["observed_at"]),
                r["sequence_number"],
                r["yes_bid_dollars"],
                r["yes_ask_dollars"],
                r["last_price_dollars"],
                r["volume_fp"],
                r["liquidity_dollars"],
            )
            for r in rr
        ]
        s=se._calculate_market(market_id=mid,rows=rows)
        f=fe._extract_market(s)
        u=ue._score_market(f)
        cand=ce._classify_market(f,u)
        adm=ae._evaluate_market(cand)
        records.append({
            "market_id":mid,
            "market":meta.get(mid,{}),
            "history_rows":len(rows),
            "statistics":_d(s),
            "features":_d(f),
            "usefulness":_d(u),
            "candidate":_d(cand),
            "admission":_d(adm),
        })

    records.sort(key=lambda x:(-float(x["admission"].get("admission_score",0) or 0),x["market_id"]))
    if not records:
        raise RuntimeError("OIAR-054 produced no analytics")

    body={
        "schema_version":"OIAR-054",
        "stage":STAGE,
        "market_count":len(records),
        "markets":records,
        "read_only_source":True,
        "execution_authority":False,
    }
    h=stable_hash(body)
    sid="oiar-054-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor()
        q.execute(
            f"""INSERT INTO public.{SNAPSHOT_TABLE}
            (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,
             payload_json,payload_hash,read_only_source,execution_authority)
            VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE)
            ON CONFLICT(snapshot_id) DO NOTHING""",
            (
                sid,STAGE,"OIAR-054",OIAR_054_BUILD_ID,datetime.now(timezone.utc),
                len(records),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h
            ),
        )
        c.commit()
    return body

def read_latest_current_trader_analytics(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor()
        q.execute("SET TRANSACTION READ ONLY")
        q.execute(
            f"""SELECT payload_json,payload_hash
            FROM public.{SNAPSHOT_TABLE}
            WHERE stage=%s
            ORDER BY generated_at DESC,persisted_at DESC
            LIMIT 1""",
            (STAGE,),
        )
        r=q.fetchone()
        c.rollback()
    if not r: return None
    p,h=r
    if isinstance(p,str): p=json.loads(p)
    if stable_hash(p)!=str(h):
        raise RuntimeError("OIAR-054 snapshot hash mismatch")
    return p

def physical_probe(root=None):
    return materialize_current_trader_analytics(root)
