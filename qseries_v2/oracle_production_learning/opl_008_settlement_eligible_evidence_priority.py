from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from hashlib import sha256
import json

from .opl_001_production_learning_foundation import (
    connect,STATE_TABLE,LEDGER_TABLE,ensure_production_learning_schema
)
from .opl_002_canonical_evidence_index import INDEX_TABLE,sync_evidence_index

OPL_008_BUILD_ID="OPL-008"
OPL_008_REVISION="OPL_008_SETTLEMENT_ELIGIBLE_EVIDENCE_PRIORITY_V1"
CACHE_TABLE="oracle_production_learning_outcome_resolution_cache"

@dataclass(frozen=True)
class EvidenceCandidate:
    ticker:str
    observation_id:str
    evidence_hash:str
    sequence_number:int
    observed_at:str
    observation_type:str

@dataclass(frozen=True)
class SettledOutcome:
    ticker:str
    result:str
    settlement_ts:str
    source_hash:str
    raw:dict

@dataclass(frozen=True)
class SettlementEligibleLearningSummary:
    evidence_candidates:int
    settlement_checked:int
    settled:int
    already_learned:int
    admitted:int
    applied:int
    production_learned_total:int
    learning_yield:float
    state_hash:str

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _credentials(root):
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    return load_kalshi_credentials(root=root)

def _get(credentials,path,params=None,timeout=15):
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
    return kalshi_rest_get(credentials,path,params or {},timeout)

def ensure_resolution_cache(root=None):
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{CACHE_TABLE}(
      ticker TEXT PRIMARY KEY,
      last_status TEXT NOT NULL DEFAULT '',
      attempts BIGINT NOT NULL DEFAULT 0,
      last_checked_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      next_check_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      last_error TEXT NOT NULL DEFAULT ''
    );
    CREATE INDEX IF NOT EXISTS oracle_production_learning_outcome_resolution_next_idx
      ON public.{CACHE_TABLE}(next_check_at);
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
    return True

def _normalize_market(raw):
    raw=dict(raw)
    ticker=str(raw.get("ticker") or "").strip().upper()
    result=str(raw.get("result") or "").strip().lower()
    settlement_ts=str(
        raw.get("settlement_ts")
        or raw.get("settled_ts")
        or raw.get("settled_time")
        or ""
    ).strip()
    status=str(raw.get("status") or "").strip().lower()

    if not ticker or status!="settled" or result not in ("yes","no","scalar") or not settlement_ts:
        return None

    return SettledOutcome(ticker,result,settlement_ts,_h(raw),raw)

def _load_state(raw):
    from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import (
        IncrementalLearnerState,genesis_incremental_state
    )
    return genesis_incremental_state() if not raw else IncrementalLearnerState(**dict(raw))

def _build_input(sequence,outcome,evidence):
    from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
    from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input

    value=True if outcome.result=="yes" else False if outcome.result=="no" else outcome.raw.get("settlement_value")
    oo=build_outcome_observation(
        outcome.ticker,"settlement",value,outcome.settlement_ts,
        "kalshi:"+outcome.ticker,outcome.source_hash
    )
    lineage=sha256((evidence.evidence_hash+outcome.source_hash).encode()).hexdigest()
    event=assemble_learning_event(outcome.ticker,evidence.evidence_hash,lineage,oo)
    ri=build_runtime_input(
        int(sequence),"learning_event",event.event_id,event.event_hash,
        {
            "subject_id":event.subject_id,
            "evidence_hash":event.evidence_hash,
            "outcome_hash":event.outcome_hash,
            "lineage_hash":event.lineage_hash,
            "outcome_type":event.outcome_type,
        }
    )
    return ri,event.event_hash

def collect_settlement_eligible_candidates(root=None,limit=5000,min_age_minutes=30):
    root=Path(root or Path.cwd()).resolve()
    ensure_resolution_cache(root)

    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                WITH ranked AS (
                    SELECT
                        ticker,
                        observation_id,
                        evidence_hash,
                        sequence_number,
                        observed_at,
                        observation_type,
                        ROW_NUMBER() OVER (
                            PARTITION BY ticker
                            ORDER BY sequence_number DESC
                        ) AS rn
                    FROM public.{INDEX_TABLE}
                    WHERE observed_at::timestamptz <=
                          clock_timestamp() - (%s || ' minutes')::interval
                )
                SELECT
                    r.ticker,
                    r.observation_id,
                    r.evidence_hash,
                    r.sequence_number,
                    r.observed_at,
                    r.observation_type
                FROM ranked r
                LEFT JOIN public.{LEDGER_TABLE} l
                  ON l.ticker=r.ticker AND l.status='LEARNED'
                LEFT JOIN public.{CACHE_TABLE} c
                  ON c.ticker=r.ticker
                WHERE r.rn=1
                  AND l.ticker IS NULL
                  AND (c.ticker IS NULL OR c.next_check_at<=clock_timestamp())
                ORDER BY r.observed_at ASC, r.sequence_number ASC
                LIMIT %s
                """,
                (int(min_age_minutes),int(limit)),
            )
            rows=cur.fetchall()

    return tuple(
        EvidenceCandidate(
            str(r[0]).upper(),
            str(r[1]),
            str(r[2]),
            int(r[3]),
            str(r[4]),
            str(r[5]),
        )
        for r in rows
    )

def _cache_resolution(root,ticker,status,error="",retry_minutes=60):
    ensure_resolution_cache(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO public.{CACHE_TABLE}
                  (ticker,last_status,attempts,last_checked_at,next_check_at,last_error)
                VALUES(%s,%s,1,clock_timestamp(),
                       clock_timestamp()+(%s || ' minutes')::interval,%s)
                ON CONFLICT(ticker) DO UPDATE SET
                  last_status=EXCLUDED.last_status,
                  attempts={CACHE_TABLE}.attempts+1,
                  last_checked_at=clock_timestamp(),
                  next_check_at=EXCLUDED.next_check_at,
                  last_error=EXCLUDED.last_error
                """,
                (str(ticker).upper(),str(status),int(retry_minutes),str(error)[:500]),
            )
        conn.commit()

def resolve_candidate(root,credentials,evidence):
    try:
        r=_get(credentials,f"/markets/{evidence.ticker}",{},15)
    except Exception as exc:
        _cache_resolution(root,evidence.ticker,"HTTP_ERROR",type(exc).__name__,240)
        return None

    body=dict(r.body or {})
    raw=body.get("market") if isinstance(body.get("market"),dict) else body
    if not isinstance(raw,dict):
        _cache_resolution(root,evidence.ticker,"INVALID_BODY","",240)
        return None

    status=str(raw.get("status") or "").strip().lower()
    if status!="settled":
        # Open/active markets should not be hammered every cycle.
        _cache_resolution(root,evidence.ticker,status or "UNRESOLVED","",30)
        return None

    outcome=_normalize_market(raw)
    if outcome is None:
        _cache_resolution(root,evidence.ticker,"SETTLED_INCOMPLETE","",120)
        return None

    if str(evidence.observed_at) >= str(outcome.settlement_ts):
        _cache_resolution(root,evidence.ticker,"POST_SETTLEMENT_EVIDENCE","",1440)
        return None

    _cache_resolution(root,evidence.ticker,"SETTLED_ELIGIBLE","",1440)
    return outcome

def collect_settled_evidence_pairs(
    root=None,
    candidate_limit=5000,
    target_settled=250,
    min_age_minutes=30,
    progress=print,
):
    root=Path(root or Path.cwd()).resolve()
    credentials=_credentials(root)
    candidates=collect_settlement_eligible_candidates(
        root,candidate_limit,min_age_minutes
    )

    checked=0
    settled=[]

    for e in candidates:
        checked+=1
        outcome=resolve_candidate(root,credentials,e)
        if outcome is not None:
            settled.append((e,outcome))

        if checked==1 or checked%100==0 or outcome is not None:
            progress(
                f"[OPL SETTLEMENT-ELIGIBLE] checked={checked} "
                f"settled={len(settled)} candidates={len(candidates)}"
            )

        if len(settled)>=int(target_settled):
            break

    return tuple(settled),len(candidates),checked

def run_settlement_eligible_learning_cycle(
    root=None,
    candidate_limit=5000,
    target_settled=250,
    min_age_minutes=30,
    progress=print,
):
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import assemble_runtime_batch
    from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle

    root=Path(root or Path.cwd()).resolve()
    ensure_production_learning_schema(root)
    ensure_resolution_cache(root)

    sync=sync_evidence_index(
        root,batch_size=5000,max_batches=10,backfill_if_empty=100000
    )

    pairs,candidate_count,checked=collect_settled_evidence_pairs(
        root=root,
        candidate_limit=candidate_limit,
        target_settled=target_settled,
        min_age_minutes=min_age_minutes,
        progress=progress,
    )

    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT production_outcomes_learned,cycles,
                       applied_through_sequence,ocl_state_json,state_hash
                FROM public.{STATE_TABLE}
                WHERE state_id=1
                FOR UPDATE
                """
            )
            prod,cycles,through,raw_state,state_hash=cur.fetchone()
            ocl=_load_state(raw_state)

            inputs=[]
            pending=[]
            already=0
            seq=int(through)

            for evidence,outcome in pairs:
                cur.execute(
                    f"SELECT status FROM public.{LEDGER_TABLE} WHERE settlement_hash=%s",
                    (outcome.source_hash,),
                )
                old=cur.fetchone()
                if old and str(old[0])=="LEARNED":
                    already+=1
                    continue

                seq+=1
                ri,event_hash=_build_input(seq,outcome,evidence)
                inputs.append(ri)
                pending.append((evidence,outcome,event_hash))

                cur.execute(
                    f"""
                    INSERT INTO public.{LEDGER_TABLE}
                    (settlement_hash,ticker,result,settlement_ts,
                     evidence_observation_id,evidence_hash,
                     evidence_sequence_number,learning_event_hash,status)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'ELIGIBLE')
                    ON CONFLICT(settlement_hash) DO UPDATE SET
                      evidence_observation_id=EXCLUDED.evidence_observation_id,
                      evidence_hash=EXCLUDED.evidence_hash,
                      evidence_sequence_number=EXCLUDED.evidence_sequence_number,
                      learning_event_hash=EXCLUDED.learning_event_hash,
                      status='ELIGIBLE',
                      updated_at=clock_timestamp()
                    """,
                    (
                        outcome.source_hash,outcome.ticker,outcome.result,
                        outcome.settlement_ts,evidence.observation_id,
                        evidence.evidence_hash,evidence.sequence_number,event_hash
                    ),
                )

            applied=0

            if inputs:
                batch=assemble_runtime_batch(tuple(inputs))
                result,new_ocl=run_learning_cycle(int(cycles)+1,ocl,batch)

                applied=len(inputs)
                prod=int(prod)+applied
                cycles=int(cycles)+1
                last=max(
                    pending,
                    key=lambda x:(x[1].settlement_ts,x[1].ticker),
                )[1]

                for evidence,outcome,event_hash in pending:
                    cur.execute(
                        f"""
                        UPDATE public.{LEDGER_TABLE}
                        SET status='LEARNED',
                            learned_at=clock_timestamp(),
                            updated_at=clock_timestamp()
                        WHERE settlement_hash=%s
                        """,
                        (outcome.source_hash,),
                    )

                cur.execute(
                    f"""
                    UPDATE public.{STATE_TABLE}
                    SET production_outcomes_learned=%s,
                        cycles=%s,
                        applied_through_sequence=%s,
                        ocl_state_json=%s::jsonb,
                        last_settlement_ts=%s,
                        last_ticker=%s,
                        state_hash=%s,
                        updated_at=clock_timestamp()
                    WHERE state_id=1
                    """,
                    (
                        prod,cycles,int(new_ocl.applied_through_sequence),
                        json.dumps(asdict(new_ocl),sort_keys=True),
                        last.settlement_ts,last.ticker,new_ocl.state_hash
                    ),
                )
                state_hash=new_ocl.state_hash

                progress(
                    f"[OPL LEARN] applied={applied} production_total={prod} "
                    f"cycle={cycles} through_sequence={new_ocl.applied_through_sequence}"
                )
                progress(
                    f"[OPL LEARN] state_hash={new_ocl.state_hash} "
                    f"cycle_hash={result.cycle_hash}"
                )

        conn.commit()

    settled_count=len(pairs)
    yield_=(applied/settled_count) if settled_count else 0.0

    progress(
        f"[OPL METRICS] evidence_candidates={candidate_count} "
        f"settlement_checked={checked} settled={settled_count} "
        f"evidence_matched={settled_count} admitted={len(inputs)} "
        f"applied={applied} learning_yield={yield_:.3f} "
        f"indexed={sync['inserted']}"
    )

    return SettlementEligibleLearningSummary(
        candidate_count,checked,settled_count,already,len(inputs),
        applied,int(prod),yield_,str(state_hash or "")
    )

def verify_opl_008_settlement_eligible_evidence_priority(root=None):
    return (
        OPL_008_BUILD_ID=="OPL-008"
        and callable(collect_settlement_eligible_candidates)
        and callable(resolve_candidate)
        and callable(run_settlement_eligible_learning_cycle)
    )
