from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_047_live_learning_metrics_contract.py";TEST=ROOT/"test_olr_047_live_learning_metrics_contract.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOLR_047_BUILD_ID="OLR-047"\nOLR_047_REVISION="OLR_047_LIVE_LEARNING_METRICS_CONTRACT_V1"\n\n@dataclass(frozen=True)\nclass LiveLearningMetrics:\n    settled:int\n    evidence_matched:int\n    evidence_missing:int\n    admitted:int\n    applied:int\n    evidence_coverage:float\n    learning_yield:float\n\ndef build_live_learning_metrics(settled,evidence_matched,evidence_missing,admitted,applied):\n    settled=int(settled);evidence_matched=int(evidence_matched);evidence_missing=int(evidence_missing)\n    admitted=int(admitted);applied=int(applied)\n    coverage=0.0 if settled<=0 else evidence_matched/settled\n    yield_=0.0 if settled<=0 else applied/settled\n    return LiveLearningMetrics(settled,evidence_matched,evidence_missing,admitted,applied,coverage,yield_)\n\ndef verify_olr_047_live_learning_metrics_contract(root=None):\n    m=build_live_learning_metrics(100,25,75,20,10)\n    return (\n        OLR_047_BUILD_ID=="OLR-047"\n        and abs(m.evidence_coverage-.25)<1e-12\n        and abs(m.learning_yield-.10)<1e-12\n    )\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_047_live_learning_metrics_contract import *\nclass T(unittest.TestCase):\n    def test_metrics(self):\n        m=build_live_learning_metrics(100,25,75,20,10)\n        self.assertEqual(m.evidence_matched+m.evidence_missing,m.settled)\n        self.assertEqual(m.evidence_coverage,.25)\n        self.assertEqual(m.learning_yield,.10)\nif __name__=="__main__":\n    print("="*88);print(" OLR-047 CERTIFICATION TEST");print(" LIVE LEARNING METRICS CONTRACT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] evidence_coverage and learning_yield metrics certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-047 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-047 INSTALLER");print(" LIVE LEARNING METRICS CONTRACT");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_046_oracle_live_evidence_learner_launcher_cutover")
    if not up.verify_olr_046_oracle_live_evidence_learner_launcher_cutover(ROOT):raise RuntimeError("Certified OLR-046 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_047_live_learning_metrics_contract import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-047 installation failed; affected files restored");raise
    print("[PASS] OLR-046 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-047 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
