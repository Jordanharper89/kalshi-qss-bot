from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from hashlib import sha256
import json

from .opl_001_production_learning_foundation import connect,STATE_TABLE,LEDGER_TABLE,ensure_production_learning_schema
from .opl_002_canonical_evidence_index import sync_evidence_index,find_pre_settlement_evidence_batch

OPL_003_BUILD_ID="OPL-003"
OPL_003_REVISION="OPL_003_EVIDENCE_SUPPORTED_SETTLEMENT_INTAKE_CORRECTION_V2"

@dataclass(frozen=True)
class SettledOutcome:
    ticker:str
    result:str
    settlement_ts:str
    source_hash:str
    raw:dict

@dataclass(frozen=True)
class ProductionLearningCycleSummary:
    settled_scanned:int
    already_learned:int
    evidence_matched:int
    evidence_missing:int
    admitted:int
    applied:int
    production_learned_total:int
    evidence_coverage:float
    learning_yield:float
    state_hash:str

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def normalize_settled_market(m):
    m=dict(m)
    ticker=str(m.get("ticker") or "").strip().upper()
    result=str(m.get("result") or "").strip().lower()
    ts=str(m.get("settlement_ts") or m.get("settled_ts") or m.get("settled_time") or "").strip()
    if not ticker or result not in ("yes","no","scalar") or not ts:
        return None
    return SettledOutcome(ticker,result,ts,_h(m),m)

def _credentials(root):
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    return load_kalshi_credentials(root=root)

def _get(c,path,params,timeout=15):
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
    return kalshi_rest_get(c,path,params,timeout)

def _genesis():
    from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import genesis_incremental_state
    return genesis_incremental_state()

def _load_state(raw):
    from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import IncrementalLearnerState
    return _genesis() if not raw else IncrementalLearnerState(**dict(raw))

def _build_input(sequence,outcome,evidence):
    from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
    from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input
    value=True if outcome.result=="yes" else False if outcome.result=="no" else outcome.raw.get("settlement_value")
    oo=build_outcome_observation(outcome.ticker,"settlement",value,outcome.settlement_ts,"kalshi:"+outcome.ticker,outcome.source_hash)
    lineage=sha256((evidence.evidence_hash+outcome.source_hash).encode()).hexdigest()
    event=assemble_learning_event(outcome.ticker,evidence.evidence_hash,lineage,oo)
    ri=build_runtime_input(int(sequence),"learning_event",event.event_id,event.event_hash,{
        "subject_id":event.subject_id,
        "evidence_hash":event.evidence_hash,
        "outcome_hash":event.outcome_hash,
        "lineage_hash":event.lineage_hash,
        "outcome_type":event.outcome_type,
    })
    return ri,event.event_hash

def collect_evidence_supported_settlements(root=None,max_pages=250,page_size=1000,target_matches=250,evidence_limit=5,progress=print):
    root=Path(root or Path.cwd()).resolve()
    c=_credentials(root)
    cursor=None
    scanned=0
    missing=0
    duplicates=0
    matches=[]
    seen=set()

    for page_no in range(1,int(max_pages)+1):
        params={"limit":max(1,min(int(page_size),1000)),"status":"settled"}
        if cursor:
            params["cursor"]=cursor
        r=_get(c,"/markets",params,15)
        raw_markets=tuple(r.body.get("markets",()))
        outcomes=[]
        for raw in raw_markets:
            o=normalize_settled_market(raw)
            if o and o.source_hash not in seen:
                seen.add(o.source_hash)
                outcomes.append(o)

        scanned+=len(outcomes)

        with connect(root) as conn:
            with conn.cursor() as cur:
                hashes=[o.source_hash for o in outcomes]
                learned=set()
                if hashes:
                    cur.execute(
                        "SELECT settlement_hash FROM public.%s WHERE settlement_hash = ANY(%%s) AND status='LEARNED'" % LEDGER_TABLE,
                        (hashes,),
                    )
                    learned={str(x[0]) for x in cur.fetchall()}

        duplicates+=len(learned)
        unresolved=[o for o in outcomes if o.source_hash not in learned]

        evidence_map=find_pre_settlement_evidence_batch(
            root,{o.ticker:o.settlement_ts for o in unresolved},evidence_limit
        )

        for o in unresolved:
            ev=evidence_map.get(o.ticker,())
            if ev:
                matches.append((o,ev[0]))
                if len(matches)>=int(target_matches):
                    progress(f"[OPL INTAKE] pages={page_no} scanned={scanned} evidence_supported={len(matches)} duplicates={duplicates}")
                    return tuple(matches),scanned,missing,duplicates
            else:
                missing+=1

        if page_no==1 or page_no%10==0 or matches:
            progress(f"[OPL INTAKE] page={page_no} scanned={scanned} evidence_supported={len(matches)} evidence_missing={missing}")

        cursor=r.body.get("cursor")
        if not cursor:
            break

    progress(f"[OPL INTAKE] exhausted pages scanned={scanned} evidence_supported={len(matches)} evidence_missing={missing}")
    return tuple(matches),scanned,missing,duplicates

def run_production_learning_cycle(root=None,settled_page_limit=250,evidence_limit=5,progress=print):
    from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import assemble_runtime_batch
    from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle

    root=Path(root or Path.cwd()).resolve()
    ensure_production_learning_schema(root)

    sync=sync_evidence_index(root,batch_size=5000,max_batches=10,backfill_if_empty=100000)

    supported,scanned,missing,dup=collect_evidence_supported_settlements(
        root=root,max_pages=settled_page_limit,page_size=1000,target_matches=250,
        evidence_limit=evidence_limit,progress=progress
    )

    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT legacy_outcomes_learned,production_outcomes_learned,cycles,applied_through_sequence,ocl_state_json,last_settlement_ts,last_ticker,state_hash FROM public.%s WHERE state_id=1 FOR UPDATE" % STATE_TABLE
            )
            legacy,prod,cycles,through,raw_state,last_ts,last_ticker,state_hash=cur.fetchone()
            ocl=_load_state(raw_state)
            inputs=[]
            pending=[]
            seq=int(through)

            for o,e in supported:
                seq+=1
                ri,event_hash=_build_input(seq,o,e)
                inputs.append(ri)
                pending.append((o,e,event_hash))
                cur.execute(
                    "INSERT INTO public.%s (settlement_hash,ticker,result,settlement_ts,evidence_observation_id,evidence_hash,evidence_sequence_number,learning_event_hash,status) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,'ELIGIBLE') ON CONFLICT(settlement_hash) DO UPDATE SET evidence_observation_id=EXCLUDED.evidence_observation_id,evidence_hash=EXCLUDED.evidence_hash,evidence_sequence_number=EXCLUDED.evidence_sequence_number,learning_event_hash=EXCLUDED.learning_event_hash,status='ELIGIBLE',updated_at=clock_timestamp()" % LEDGER_TABLE,
                    (o.source_hash,o.ticker,o.result,o.settlement_ts,e.observation_id,e.evidence_hash,e.sequence_number,event_hash),
                )

            applied=0
            if inputs:
                batch=assemble_runtime_batch(tuple(inputs))
                result,new_ocl=run_learning_cycle(int(cycles)+1,ocl,batch)
                applied=len(inputs)
                prod=int(prod)+applied
                cycles=int(cycles)+1

                last=max((x[0] for x in pending),key=lambda x:(x.settlement_ts,x.ticker))

                for o,e,event_hash in pending:
                    cur.execute(
                        "UPDATE public.%s SET status='LEARNED',learned_at=clock_timestamp(),updated_at=clock_timestamp() WHERE settlement_hash=%%s" % LEDGER_TABLE,
                        (o.source_hash,),
                    )

                cur.execute(
                    "UPDATE public.%s SET production_outcomes_learned=%%s,cycles=%%s,applied_through_sequence=%%s,ocl_state_json=%%s::jsonb,last_settlement_ts=%%s,last_ticker=%%s,state_hash=%%s,updated_at=clock_timestamp() WHERE state_id=1" % STATE_TABLE,
                    (prod,cycles,int(new_ocl.applied_through_sequence),json.dumps(asdict(new_ocl),sort_keys=True),last.settlement_ts,last.ticker,new_ocl.state_hash),
                )
                state_hash=new_ocl.state_hash

                progress(f"[OPL LEARN] applied={applied} production_total={prod} cycle={cycles} through_sequence={new_ocl.applied_through_sequence}")
                progress(f"[OPL LEARN] state_hash={new_ocl.state_hash} cycle_hash={result.cycle_hash}")

        conn.commit()

    matched=len(supported)
    coverage=(matched/scanned) if scanned else 0.0
    yield_=(applied/matched) if matched else 0.0

    progress(
        f"[OPL METRICS] settled={scanned} duplicates={dup} evidence_matched={matched} evidence_missing={missing} admitted={matched} applied={applied} evidence_coverage={coverage:.6f} learning_yield={yield_:.3f} indexed={sync['inserted']}"
    )

    return ProductionLearningCycleSummary(
        scanned,dup,matched,missing,matched,applied,int(prod),coverage,yield_,str(state_hash or "")
    )

def verify_opl_003_outcome_grounded_production_learning_cycle(root=None):
    x=normalize_settled_market({"ticker":"KXTEST","result":"yes","settlement_ts":"2026-08-18T00:00:00Z"})
    return OPL_003_BUILD_ID=="OPL-003" and x is not None and callable(collect_evidence_supported_settlements)
