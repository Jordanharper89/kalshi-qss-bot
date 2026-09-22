
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_075b_ast_crash_safe_same_writer_cutover import recover_or_prepare, finalize
from dataclasses import dataclass
from pathlib import Path
from .olr_002_settled_outcome_read_model import fetch_recent_settled_markets
from .olr_003_learning_event_bridge import build_learning_runtime_input
from .olr_004_learning_cycle_state import load_learning_runtime_state,save_learning_runtime_state,apply_learning_inputs
from .olr_006_historical_evidence_matcher import find_historical_market_evidence
from .olr_007_learning_event_ledger import LearningLedgerRecord,load_learning_ledger,save_learning_ledger
from .olr_008_learning_coverage_metrics import build_learning_coverage_metrics
OLR_009_BUILD_ID="OLR-009";OLR_009_REVISION="OLR_009_HIGH_COVERAGE_LEARNING_CYCLE_V1"
@dataclass(frozen=True)
class HighCoverageLearningCycleSummary:
    metrics:object;learned_total:int;state_hash:str;idle:bool
def run_high_coverage_learning_cycle(root=None,settled_limit=100,evidence_limit=3,progress=print):
    root=Path(root or Path.cwd());sp=root/"runtime_state"/"oracle_learning_runtime_state.json";lp=root/"runtime_state"/"oracle_learning_event_ledger.json"
    state=load_learning_runtime_state(sp);ledger=load_learning_ledger(lp);outcomes=fetch_recent_settled_markets(root,limit=settled_limit)
    dup=matched=missing=admitted=0;inputs=[];pending=[];seq=state.ocl_state.applied_through_sequence
    for o in outcomes:
        old=ledger.get(o.source_hash)
        if old and old.status=="learned":dup+=1;continue
        matches=find_historical_market_evidence(root,o.ticker,limit=evidence_limit)
        if not matches:
            missing+=1;ledger[o.source_hash]=LearningLedgerRecord(o.source_hash,o.ticker,o.settlement_ts,"evidence_missing","","");continue
        matched+=1;e=matches[0];seq+=1;ri=build_learning_runtime_input(seq,o,e.evidence_hash)
        if old and old.learning_event_hash==ri.source_hash:continue
        ledger[o.source_hash]=LearningLedgerRecord(o.source_hash,o.ticker,o.settlement_ts,"eligible",e.evidence_hash,ri.source_hash)
        inputs.append(ri);pending.append(o);admitted+=1
    applied=0
    if inputs:
        last=max(pending,key=lambda x:(x.settlement_ts,x.ticker));result,state=apply_learning_inputs(state,tuple(inputs),last.settlement_ts,last.ticker);save_learning_runtime_state(sp,state);applied=len(inputs)
        for o in pending:
            r=ledger[o.source_hash];ledger[o.source_hash]=LearningLedgerRecord(r.settlement_hash,r.ticker,r.settlement_ts,"learned",r.evidence_hash,r.learning_event_hash)
        progress(f"[LEARN] outcomes={applied} cycle={state.cycles} learned_total={state.outcomes_learned} through_sequence={state.ocl_state.applied_through_sequence}")
        progress(f"[LEARN] state_hash={state.ocl_state.state_hash} cycle_hash={result.cycle_hash}")
    slop_mode, slop_state, slop_rows, slop_journal = recover_or_prepare(state, root, progress)
    if slop_mode == "APPLY":
        state = slop_state
        save_learning_runtime_state(sp, state)
        finalize(slop_rows, root, progress)
        progress(f"[SLOP LEARN CUTOVER] applied={len(slop_rows)} crash_safe=True")
    elif slop_mode == "RECOVER_COMMIT":
        finalize(tuple(), root, progress)
        progress("[SLOP LEARN CUTOVER] recovered durable learner-state commit")
    save_learning_ledger(lp,ledger)
    metrics=build_learning_coverage_metrics(len(outcomes),dup,matched,missing,admitted,applied)
    progress(f"[LEARN METRICS] settled={metrics.settled_scanned} duplicates={metrics.duplicate_settlements} evidence_matched={metrics.evidence_matched} evidence_missing={metrics.evidence_missing} applied={metrics.learning_events_applied} evidence_coverage={metrics.evidence_coverage:.3f} learning_yield={metrics.learning_yield:.3f}")
    if not applied:progress("[LEARN] idle no_new_eligible_outcome_grounded_learning_events")
    return HighCoverageLearningCycleSummary(metrics,state.outcomes_learned,state.ocl_state.state_hash,applied==0)
def verify_olr_009_high_coverage_learning_cycle():return callable(run_high_coverage_learning_cycle)
