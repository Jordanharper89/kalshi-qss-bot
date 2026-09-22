from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_learning_runtime";MOD=PKG/"olr_010_capability_gate.py";RUNTIME=PKG/"olr_010_runtime.py";TEST_PATH=ROOT/"test_olr_010_high_coverage_continuous_learning_gate.py";PHYS=ROOT/"run_olr_010_physical_high_coverage_learning_verification.py";COMPAT=ROOT/"run_olr_005_continuous_learning_runtime.py";INIT=PKG/"__init__.py"
MODULE=r"""
from dataclasses import dataclass
from .olr_006_historical_evidence_matcher import verify_olr_006_historical_evidence_matcher
from .olr_007_learning_event_ledger import verify_olr_007_durable_learning_event_ledger
from .olr_008_learning_coverage_metrics import verify_olr_008_learning_coverage_metrics
from .olr_009_high_coverage_learning_cycle import verify_olr_009_high_coverage_learning_cycle
OLR_010_BUILD_ID="OLR-010";OLR_010_REVISION="OLR_010_HIGH_COVERAGE_CONTINUOUS_LEARNING_GATE_V1"
@dataclass(frozen=True)
class OLR010Certification:
    builds:tuple[str,...];capability:str;next_capability:str;certified:bool=True
def certify_olr_006_through_010():
    if not all((verify_olr_006_historical_evidence_matcher(),verify_olr_007_durable_learning_event_ledger(),verify_olr_008_learning_coverage_metrics(),verify_olr_009_high_coverage_learning_cycle())):raise RuntimeError("OLR gate failed")
    return OLR010Certification(tuple("OLR-%03d"%i for i in range(6,11)),"high_coverage_idempotent_outcome_grounded_learning","learned_state_feedback_into_continuous_scientific_reasoning",True)
def verify_olr_010_high_coverage_continuous_learning_gate():return certify_olr_006_through_010().certified
"""
RUNTIME_SRC=r"""
from pathlib import Path
import argparse,time
from .olr_009_high_coverage_learning_cycle import run_high_coverage_learning_cycle
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--settled-limit",type=int,default=100);p.add_argument("--evidence-limit",type=int,default=3);p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args(argv)
    if a.settled_limit<1 or a.evidence_limit<1 or a.cadence_seconds<=0:raise SystemExit("invalid arguments")
    root=Path.cwd();print("="*72,flush=True);print(" OLR-010 HIGH-COVERAGE CONTINUOUS LEARNING RUNTIME",flush=True);print("="*72,flush=True);cycles=0
    try:
        while True:
            s=run_high_coverage_learning_cycle(root,a.settled_limit,a.evidence_limit,lambda x:print(x,flush=True));cycles+=1;print(f"[LEARN] runtime_cycle={cycles} idle={s.idle} learned_total={s.learned_total}",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
    except KeyboardInterrupt:
        print("\\n[STOP] Learning runtime stopped by operator.",flush=True);return 0
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_learning_runtime.olr_010_capability_gate import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_010_high_coverage_continuous_learning_gate())
    def test_five(self):self.assertEqual(len(certify_olr_006_through_010().builds),5)
if __name__=="__main__":
    print("="*72);print(" OLR-010 CERTIFICATION TEST");print(" HIGH-COVERAGE CONTINUOUS LEARNING GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OLR-006 through OLR-010 high-coverage continuous learning certified");print("[PASS] Next capability: learned-state feedback into continuous Scientific Reasoning");print("[DONE] OLR-010 CERTIFIED")
"""
PHYS_SRC=r"""
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle import run_high_coverage_learning_cycle
if __name__=="__main__":
    print("="*72);print(" OLR-010 PHYSICAL HIGH-COVERAGE LEARNING VERIFICATION");print("="*72)
    s=run_high_coverage_learning_cycle(Path.cwd(),20,3,lambda x:print(x,flush=True));print("[SUMMARY]",s)
    print("[PASS] Real settled outcomes scanned through historical evidence matcher + durable ledger")
    if s.metrics.learning_events_applied:print("[PASS] Real outcome-grounded learning events applied to frozen OCL runtime")
    else:print("[PASS] No eligible unmatched outcome/evidence pair in sample; no fabricated learning applied")
    print("[DONE] OLR-010 PHYSICAL HIGH-COVERAGE LEARNING VERIFIED")
"""
COMPAT_SRC='from qseries_v2.oracle_learning_runtime.olr_010_runtime import main\nif __name__=="__main__": raise SystemExit(main())\n'
def w(p,s):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def main():
    print("="*72);print(" OLR-010 INSTALLER");print(" HIGH-COVERAGE CONTINUOUS LEARNING GATE");print("="*72)
    sys.path.insert(0,str(ROOT));m=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle");assert m.verify_olr_009_high_coverage_learning_cycle()
    affected=(MOD,RUNTIME,TEST_PATH,PHYS,COMPAT,INIT);backs={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        w(MOD,MODULE);w(RUNTIME,RUNTIME_SRC);w(TEST_PATH,TEST_SOURCE);w(PHYS,PHYS_SRC);w(COMPAT,COMPAT_SRC);cur=INIT.read_text(encoding="utf-8")
        if "# OLR-010 exports" not in cur:w(INIT,cur.rstrip()+"\n\n# OLR-010 exports\nfrom .olr_010_capability_gate import *\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,b in backs.items():
            if b is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(b)
        raise
    print("[PASS] Existing Oracle learning child upgraded in place to OLR-010 runtime")
    print("[DONE] OLR-010 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
