from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from hashlib import sha256
import json

from .opl_001_production_learning_foundation import (
    connect,STATE_TABLE,LEDGER_TABLE,ensure_production_learning_schema
)
from .opl_002_canonical_evidence_index import (
    INDEX_TABLE,
    sync_evidence_index,
)

OPL_007_BUILD_ID="OPL-007"
OPL_007_REVISION="OPL_007_EVIDENCE_FIRST_OUTCOME_RESOLVER_V1"

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
class EvidenceFirstLearningSummary:
    evidence_candidates:int
    settlement_checked:int
    settled:int
    already_learned:int
    evidence_matched:int
    admitted:int
    applied:int
    production_learned_total:int
    learning_yield:float
    state_hash:str

def _h(v):
    return sha256(
        json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()

def _credentials(root):
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    return load_kalshi_credentials(root=root)

def _get(credentials,path,params=None,timeout=15):
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
    return kalshi_rest_get(credentials,path,params or {},timeout)

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

    if not ticker:
        return None
    if status!="settled":
        return None
    if result not in ("yes","no","scalar"):
        return None
    if not settlement_ts:
        return None

    return SettledOutcome(
        ticker=ticker,
        result=result,
        settlement_ts=settlement_ts,
        source_hash=_h(raw),
        raw=raw,
    )

def _load_ocl_state(raw):
    from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import (
        IncrementalLearnerState,
        genesis_incremental_state,
    )
    if not raw:
        return genesis_incremental_state()
    return IncrementalLearnerState(**dict(raw))

def _build_runtime_input(sequence,outcome,evidence):
    from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import (
        build_outcome_observation,
    )
    from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import (
        assemble_learning_event,
    )
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import (
        build_runtime_input,
    )

    value=(
        True if outcome.result=="yes"
        else False if outcome.result=="no"
        else outcome.raw.get("settlement_value")
    )

    oo=build_outcome_observation(
        outcome.ticker,
        "settlement",
        value,
        outcome.settlement_ts,
        "kalshi:"+outcome.ticker,
        outcome.source_hash,
    )

    lineage=sha256(
        (evidence.evidence_hash+outcome.source_hash).encode()
    ).hexdigest()

    event=assemble_learning_event(
        outcome.ticker,
        evidence.evidence_hash,
        lineage,
        oo,
    )

    ri=build_runtime_input(
        int(sequence),
        "learning_event",
        event.event_id,
        event.event_hash,
        {
            "subject_id":event.subject_id,
            "evidence_hash":event.evidence_hash,
            "outcome_hash":event.outcome_hash,
            "lineage_hash":event.lineage_hash,
            "outcome_type":event.outcome_type,
        },
    )
    return ri,event.event_hash

def collect_evidence_candidates(root=None,limit=5000):
    root=Path(root or Path.cwd()).resolve()
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
                    ON l.ticker=r.ticker
                   AND l.status='LEARNED'
                WHERE r.rn=1
                  AND l.ticker IS NULL
                ORDER BY r.sequence_number DESC
                LIMIT %s
                """,
                (int(limit),),
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

def resolve_settlement(credentials,ticker):
    ticker=str(ticker).strip().upper()
    if not ticker:
        return None

    r=_get(credentials,f"/markets/{ticker}",{},15)
    body=dict(r.body or {})
    raw=body.get("market") if isinstance(body.get("market"),dict) else body
    if not isinstance(raw,dict):
        return None

    return _normalize_market(raw)

def collect_evidence_supported_settlements(
    root=None,
    candidate_limit=5000,
    target_settled=250,
    progress=print,
):
    root=Path(root or Path.cwd()).resolve()
    credentials=_credentials(root)
    candidates=collect_evidence_candidates(root,candidate_limit)

    checked=0
    settled=[]
    missing=0

    for i,e in enumerate(candidates,1):
        checked+=1
        try:
            outcome=resolve_settlement(credentials,e.ticker)
        except Exception as exc:
            progress(
                f"[OPL EVIDENCE-FIRST] settlement_lookup_error "
                f"ticker={e.ticker} type={type(exc).__name__}"
            )
            continue

        if outcome is None:
            missing+=1
        else:
            # Enforce strict pre-settlement evidence.
            if str(e.observed_at) < str(outcome.settlement_ts):
                settled.append((e,outcome))

        if i==1 or i%100==0 or settled:
            progress(
                f"[OPL EVIDENCE-FIRST] checked={checked} "
                f"settled={len(settled)} unresolved={missing}"
            )

        if len(settled)>=int(target_settled):
            break

    return tuple(settled),len(candidates),checked,missing

def run_evidence_first_learning_cycle(
    root=None,
    candidate_limit=5000,
    target_settled=250,
    progress=print,
):
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import (
        assemble_runtime_batch,
    )
    from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import (
        run_learning_cycle,
    )

    root=Path(root or Path.cwd()).resolve()
    ensure_production_learning_schema(root)

    sync=sync_evidence_index(
        root,
        batch_size=5000,
        max_batches=10,
        backfill_if_empty=100000,
    )

    supported,candidate_count,checked,unresolved=collect_evidence_supported_settlements(
        root=root,
        candidate_limit=candidate_limit,
        target_settled=target_settled,
        progress=progress,
    )

    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    production_outcomes_learned,
                    cycles,
                    applied_through_sequence,
                    ocl_state_json,
                    state_hash
                FROM public.{STATE_TABLE}
                WHERE state_id=1
                FOR UPDATE
                """
            )
            prod,cycles,through,raw_state,state_hash=cur.fetchone()
            ocl=_load_ocl_state(raw_state)

            inputs=[]
            pending=[]
            seq=int(through)
            already_learned=0

            for evidence,outcome in supported:
                cur.execute(
                    f"""
                    SELECT status
                    FROM public.{LEDGER_TABLE}
                    WHERE settlement_hash=%s
                    """,
                    (outcome.source_hash,),
                )
                old=cur.fetchone()
                if old and str(old[0])=="LEARNED":
                    already_learned+=1
                    continue

                seq+=1
                ri,event_hash=_build_runtime_input(seq,outcome,evidence)
                inputs.append(ri)
                pending.append((evidence,outcome,event_hash))

                cur.execute(
                    f"""
                    INSERT INTO public.{LEDGER_TABLE}
                    (
                        settlement_hash,ticker,result,settlement_ts,
                        evidence_observation_id,evidence_hash,
                        evidence_sequence_number,learning_event_hash,status
                    )
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
                        outcome.source_hash,
                        outcome.ticker,
                        outcome.result,
                        outcome.settlement_ts,
                        evidence.observation_id,
                        evidence.evidence_hash,
                        evidence.sequence_number,
                        event_hash,
                    ),
                )

            applied=0

            if inputs:
                batch=assemble_runtime_batch(tuple(inputs))
                result,new_ocl=run_learning_cycle(
                    int(cycles)+1,
                    ocl,
                    batch,
                )

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
                        SET
                            status='LEARNED',
                            learned_at=clock_timestamp(),
                            updated_at=clock_timestamp()
                        WHERE settlement_hash=%s
                        """,
                        (outcome.source_hash,),
                    )

                cur.execute(
                    f"""
                    UPDATE public.{STATE_TABLE}
                    SET
                        production_outcomes_learned=%s,
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
                        prod,
                        cycles,
                        int(new_ocl.applied_through_sequence),
                        json.dumps(asdict(new_ocl),sort_keys=True),
                        last.settlement_ts,
                        last.ticker,
                        new_ocl.state_hash,
                    ),
                )

                state_hash=new_ocl.state_hash

                progress(
                    f"[OPL LEARN] applied={applied} "
                    f"production_total={prod} cycle={cycles} "
                    f"through_sequence={new_ocl.applied_through_sequence}"
                )
                progress(
                    f"[OPL LEARN] state_hash={new_ocl.state_hash} "
                    f"cycle_hash={result.cycle_hash}"
                )

        conn.commit()

    settled_count=len(supported)
    yield_=(applied/settled_count) if settled_count else 0.0

    progress(
        f"[OPL METRICS] evidence_candidates={candidate_count} "
        f"settlement_checked={checked} settled={settled_count} "
        f"evidence_matched={settled_count} admitted={len(inputs)} "
        f"applied={applied} learning_yield={yield_:.3f} "
        f"indexed={sync['inserted']}"
    )

    return EvidenceFirstLearningSummary(
        candidate_count,
        checked,
        settled_count,
        already_learned,
        settled_count,
        len(inputs),
        applied,
        int(prod),
        yield_,
        str(state_hash or ""),
    )

def verify_opl_007_evidence_first_outcome_resolver(root=None):
    return (
        OPL_007_BUILD_ID=="OPL-007"
        and callable(collect_evidence_candidates)
        and callable(resolve_settlement)
        and callable(run_evidence_first_learning_cycle)
    )
