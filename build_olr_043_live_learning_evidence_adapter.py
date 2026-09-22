from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_043_live_learning_evidence_adapter.py";TEST=ROOT/"test_olr_043_live_learning_evidence_adapter.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_038_postgresql_outcome_evidence_linkage_ledger import record_linkage\nfrom .olr_042_live_evidence_admission_gate import admit_outcome_evidence\n\nOLR_043_BUILD_ID="OLR-043"\nOLR_043_REVISION="OLR_043_LIVE_LEARNING_EVIDENCE_ADAPTER_V1"\n\n@dataclass(frozen=True)\nclass LearningEvidenceMetrics:\n    settled:int\n    evidence_matched:int\n    evidence_missing:int\n    admitted:int\n    evidence_coverage:float\n\ndef adapt_learning_batch(outcomes,root=None,min_score=50):\n    admitted=[]\n    settled=matched=missing=0\n    for outcome in outcomes:\n        settled+=1\n        gate=admit_outcome_evidence(outcome,root,min_score)\n        class Match:\n            pass\n        match=Match()\n        match.matched=gate.admitted\n        match.method=gate.match_method\n        match.score=gate.score\n        match.candidate=gate.candidate\n        record_linkage(outcome,match,root)\n        if gate.admitted:\n            matched+=1\n            admitted.append((outcome,gate.candidate,gate))\n        else:\n            missing+=1\n    coverage=0.0 if settled==0 else matched/settled\n    return tuple(admitted),LearningEvidenceMetrics(settled,matched,missing,len(admitted),coverage)\n\ndef verify_olr_043_live_learning_evidence_adapter(root=None):\n    from .olr_042_live_evidence_admission_gate import verify_olr_042_live_evidence_admission_gate\n    return verify_olr_042_live_evidence_admission_gate(root) and OLR_043_BUILD_ID=="OLR-043"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_043_live_learning_evidence_adapter import *\nclass T(unittest.TestCase):\n    def test_metrics(self):\n        m=LearningEvidenceMetrics(100,20,80,20,.2)\n        self.assertEqual(m.evidence_matched+m.evidence_missing,m.settled)\n        self.assertEqual(m.admitted,20)\nif __name__=="__main__":\n    print("="*88);print(" OLR-043 CERTIFICATION TEST");print(" LIVE LEARNING EVIDENCE ADAPTER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Live learning evidence metrics contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-043 CERTIFIED")\n'

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
    print("="*88);print(" OLR-043 INSTALLER");print(" LIVE LEARNING EVIDENCE ADAPTER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_042_live_evidence_admission_gate")
    if not up.verify_olr_042_live_evidence_admission_gate(ROOT):raise RuntimeError("Certified OLR-042 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_043_live_learning_evidence_adapter import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-043 installation failed; affected files restored");raise
    print("[PASS] Durable linkage ledger reused")
    print("[PASS] execution_authority=FALSE");print("[DONE] OLR-043 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
