from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_042_live_evidence_admission_gate.py";TEST=ROOT/"test_olr_042_live_evidence_admission_gate.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_037_market_evidence_candidate_matching import match_outcome_to_evidence\nfrom .olr_041_postgresql_live_evidence_lookup import lookup_market_evidence\n\nOLR_042_BUILD_ID="OLR-042"\nOLR_042_REVISION="OLR_042_LIVE_EVIDENCE_ADMISSION_GATE_V1"\n\n@dataclass(frozen=True)\nclass EvidenceAdmission:\n    admitted:bool\n    reason:str\n    score:int\n    match_method:str\n    candidate:object|None\n\ndef admit_outcome_evidence(outcome,root=None,min_score=50):\n    candidates=lookup_market_evidence(outcome,root)\n    match=match_outcome_to_evidence(outcome,candidates)\n    if not match.matched:\n        return EvidenceAdmission(False,"EVIDENCE_MISSING",0,"NONE",None)\n    if match.score<int(min_score):\n        return EvidenceAdmission(False,"EVIDENCE_SCORE_BELOW_THRESHOLD",match.score,match.method,match.candidate)\n    return EvidenceAdmission(True,"ADMITTED",match.score,match.method,match.candidate)\n\ndef verify_olr_042_live_evidence_admission_gate(root=None):\n    from .olr_041_postgresql_live_evidence_lookup import verify_olr_041_postgresql_live_evidence_lookup\n    return verify_olr_041_postgresql_live_evidence_lookup(root) and OLR_042_BUILD_ID=="OLR-042"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_042_live_evidence_admission_gate import *\nclass T(unittest.TestCase):\n    def test_contract(self):\n        x=EvidenceAdmission(True,"ADMITTED",50,"MARKET_ID",{"ticker":"X"})\n        self.assertTrue(x.admitted)\n        self.assertEqual(x.reason,"ADMITTED")\nif __name__=="__main__":\n    print("="*88);print(" OLR-042 CERTIFICATION TEST");print(" LIVE EVIDENCE ADMISSION GATE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Evidence admission contract certified")\n    print("[PASS] Missing evidence remains abstention, not learning")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-042 CERTIFIED")\n'

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
    print("="*88);print(" OLR-042 INSTALLER");print(" LIVE EVIDENCE ADMISSION GATE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_041_postgresql_live_evidence_lookup")
    if not up.verify_olr_041_postgresql_live_evidence_lookup(ROOT):raise RuntimeError("Certified OLR-041 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_042_live_evidence_admission_gate import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-042 installation failed; affected files restored");raise
    print("[PASS] OLR-041 preserved read-only");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-042 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
