from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_learning_runtime";MOD=PKG/"olr_009_high_coverage_learning_cycle.py";TEST_PATH=ROOT/"test_olr_009_high_coverage_learning_cycle.py";INIT=PKG/"__init__.py"
MODULE=r"""
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
    save_learning_ledger(lp,ledger)
    metrics=build_learning_coverage_metrics(len(outcomes),dup,matched,missing,admitted,applied)
    progress(f"[LEARN METRICS] settled={metrics.settled_scanned} duplicates={metrics.duplicate_settlements} evidence_matched={metrics.evidence_matched} evidence_missing={metrics.evidence_missing} applied={metrics.learning_events_applied} evidence_coverage={metrics.evidence_coverage:.3f} learning_yield={metrics.learning_yield:.3f}")
    if not applied:progress("[LEARN] idle no_new_eligible_outcome_grounded_learning_events")
    return HighCoverageLearningCycleSummary(metrics,state.outcomes_learned,state.ocl_state.state_hash,applied==0)
def verify_olr_009_high_coverage_learning_cycle():return callable(run_high_coverage_learning_cycle)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_009_high_coverage_learning_cycle())
if __name__=="__main__":
    print("="*72);print(" OLR-009 CERTIFICATION TEST");print(" HIGH-COVERAGE LEARNING CYCLE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Historical evidence + durable idempotent learning cycle certified");print("[DONE] OLR-009 CERTIFIED")
"""
def w(p,s):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def main():
    print("="*72);print(" OLR-009 INSTALLER");print(" HIGH-COVERAGE LEARNING CYCLE");print("="*72)
    sys.path.insert(0,str(ROOT));m=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_008_learning_coverage_metrics");assert m.verify_olr_008_learning_coverage_metrics()
    backs={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in (MOD,TEST_PATH,INIT)}
    try:
        w(MOD,MODULE);w(TEST_PATH,TEST_SOURCE);cur=INIT.read_text(encoding="utf-8")
        if "# OLR-009 exports" not in cur:w(INIT,cur.rstrip()+"\n\n# OLR-009 exports\nfrom .olr_009_high_coverage_learning_cycle import *\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,b in backs.items():
            if b is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(b)
        raise
    print("[DONE] OLR-009 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
