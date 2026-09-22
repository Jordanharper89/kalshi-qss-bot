from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import learn_calibration

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

FORECAST_SOURCES=(
    "source.crypto.prospective_forecast.btc",
    "source.crypto.prospective_forecast.eth",
    "source.crypto.prospective_forecast.sol",
)
LEARNED_SOURCES=(
    "source.crypto.learned_case.btc",
    "source.crypto.learned_case.eth",
    "source.crypto.learned_case.sol",
)
SOURCE_BY_ASSET={"BTC":LEARNED_SOURCES[0],"ETH":LEARNED_SOURCES[1],"SOL":LEARNED_SOURCES[2]}

@dataclass(frozen=True,slots=True)
class ProspectiveScoredCase:
    forecast_id:str
    asset:str
    forecast_probability:float
    outcome_positive:bool
    brier_score:float
    baseline_brier:float
    performance_delta:float
    source_correctness:tuple
    learning_event_hash:str
    outcome_hash:str

def _payload(x):
    return x if isinstance(x,dict) else dict(x or ())

def _dt(x):
    if isinstance(x,datetime):
        return x
    return datetime.fromisoformat(str(x).replace("Z","+00:00"))

def _read_latest_by_source(cur,source_id,limit):
    cur.execute(
        """SELECT sequence_number,observed_at,observation_type,
                  COALESCE(canonical_observation_json->'raw_observation'->'payload',
                           canonical_observation_json->'payload','{}'::jsonb)
           FROM public.oracle_canonical_observations
           WHERE source_id=%s
           ORDER BY sequence_number DESC
           LIMIT %s""",
        (source_id,int(limit)),
    )
    return tuple(cur.fetchall() or ())

def read_and_score_mature_prospective_cases(root=None,per_source_limit=512):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            forecast_rows=[]
            learned_rows={}
            for source in FORECAST_SOURCES:
                forecast_rows.extend(_read_latest_by_source(q,source,per_source_limit))
            for source in LEARNED_SOURCES:
                learned_rows[source]=_read_latest_by_source(q,source,per_source_limit)
        c.rollback()

    forecasts=[]
    for seq,observed,otype,raw in forecast_rows:
        if str(otype)!="crypto_prospective_internal_forecast":
            continue
        p=_payload(raw)
        if p.get("forecast_id") and p.get("created_at") and p.get("asset"):
            forecasts.append((int(seq),observed,p))
    forecasts.sort(key=lambda x:x[0])

    out=[]
    for fseq,fobs,f in forecasts:
        asset=str(f.get("asset") or "").upper()
        learned_source=SOURCE_BY_ASSET.get(asset)
        if not learned_source:
            continue
        created=_dt(f["created_at"])
        candidates=[]
        for lseq,lobs,ltype,lraw in learned_rows.get(learned_source,()):
            if str(ltype)!="crypto_verified_learned_case":
                continue
            p=_payload(lraw)
            if str(p.get("asset") or "").upper()!=asset or p.get("return_fraction") is None:
                continue
            snap_raw=p.get("snapshot_at")
            if not snap_raw:
                continue
            snap=_dt(snap_raw)
            if snap>=created:
                candidates.append((snap,int(lseq),p))
        if not candidates:
            continue

        snap,lseq,p=min(candidates,key=lambda x:(x[0],x[1]))
        prob=float(f["internal_forecast_probability"])
        if not 0.0<=prob<=1.0:
            raise RuntimeError("prospective forecast probability outside [0,1]")
        positive=float(p["return_fraction"])>0

        evidence_hash=str(p.get("evidence_hash") or "")
        outcome_hash=str(p.get("outcome_hash") or "")
        lineage_hash=str(p.get("lineage_hash") or "")
        outcome_observed_at=str(p.get("outcome_observed_at") or "")
        if len(evidence_hash)!=64 or len(outcome_hash)!=64 or len(lineage_hash)!=64 or not outcome_observed_at:
            continue

        outcome=build_outcome_observation(
            asset,
            "prospective_positive_return_60s",
            1 if positive else 0,
            outcome_observed_at,
            f"prospective:{f['forecast_id']}",
            outcome_hash,
        )
        event=assemble_learning_event(asset,evidence_hash,lineage_hash,outcome)
        if not verify_learning_event(event):
            raise RuntimeError("prospective learning event invalid")
        cal=learn_calibration(event,prob,positive)
        baseline=(.5-(1.0 if positive else 0.0))**2
        correctness=tuple(
            (str(fam),bool(pred)==positive)
            for fam,cnt,fp,pred in tuple(f.get("source_claims") or ())
        )
        out.append(ProspectiveScoredCase(
            str(f["forecast_id"]),asset,prob,positive,
            float(cal.brier_score),baseline,baseline-float(cal.brier_score),
            correctness,event.event_hash,outcome.outcome_hash,
        ))
    return tuple(out)
