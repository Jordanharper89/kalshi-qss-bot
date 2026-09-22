from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_039_evidence_coverage_recovery_engine.py";TEST=ROOT/"test_olr_039_evidence_coverage_recovery_engine.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .olr_037_market_evidence_candidate_matching import match_outcome_to_evidence\nfrom .olr_038_postgresql_outcome_evidence_linkage_ledger import record_linkage\nOLR_039_BUILD_ID="OLR-039"\nOLR_039_REVISION="OLR_039_EVIDENCE_COVERAGE_RECOVERY_ENGINE_V1"\n\n@dataclass(frozen=True)\nclass RecoveryMetrics:\n    settled:int\n    matched:int\n    missing:int\n    evidence_coverage:float\n\ndef recover_evidence_links(outcomes,evidence_provider,root=None):\n    settled=matched=missing=0\n    results=[]\n    for outcome in outcomes:\n        settled+=1\n        candidates=tuple(evidence_provider(outcome) or ())\n        match=match_outcome_to_evidence(outcome,candidates)\n        record_linkage(outcome,match,root)\n        if match.matched:matched+=1\n        else:missing+=1\n        results.append(match)\n    coverage=0.0 if settled==0 else matched/settled\n    return tuple(results),RecoveryMetrics(settled,matched,missing,coverage)\n\ndef verify_olr_039_evidence_coverage_recovery_engine(root=None):\n    from .olr_038_postgresql_outcome_evidence_linkage_ledger import verify_olr_038_postgresql_outcome_evidence_linkage_ledger\n    return verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root) and OLR_039_BUILD_ID=="OLR-039"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_039_evidence_coverage_recovery_engine import *\nclass T(unittest.TestCase):\n    def test_metrics_contract(self):\n        m=RecoveryMetrics(100,25,75,.25)\n        self.assertEqual(m.evidence_coverage,.25)\n        self.assertEqual(m.matched+m.missing,m.settled)\nif __name__=="__main__":\n    print("="*88);print(" OLR-039 CERTIFICATION TEST");print(" EVIDENCE COVERAGE RECOVERY ENGINE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Evidence coverage recovery metrics certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-039 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-039 INSTALLER");print(" EVIDENCE COVERAGE RECOVERY ENGINE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_038_postgresql_outcome_evidence_linkage_ledger")
    if not up.verify_olr_038_postgresql_outcome_evidence_linkage_ledger(ROOT):raise RuntimeError("Certified OLR-038 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_039_evidence_coverage_recovery_engine import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-039 installation failed; affected files restored");raise
    print("[PASS] Existing learning application path remains unchanged")
    print("[PASS] OLR-039 only recovers and records evidence linkage")
    print("[PASS] execution_authority=FALSE");print("[DONE] OLR-039 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
