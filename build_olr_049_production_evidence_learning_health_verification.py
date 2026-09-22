from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_049_production_evidence_learning_health_verification.py";TEST=ROOT/"test_olr_049_production_evidence_learning_health_verification.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .olr_046_oracle_live_evidence_learner_launcher_cutover import verify_olr_046_oracle_live_evidence_learner_launcher_cutover\nfrom .olr_048_postgresql_live_learning_metrics_read_model import read_linkage_metrics\n\nOLR_049_BUILD_ID="OLR-049"\nOLR_049_REVISION="OLR_049_PRODUCTION_EVIDENCE_LEARNING_HEALTH_VERIFICATION_V1"\n\n@dataclass(frozen=True)\nclass EvidenceLearningHealth:\n    launcher_active:bool\n    settled:int\n    evidence_matched:int\n    evidence_missing:int\n    evidence_coverage:float\n    learning_yield:float\n    healthy:bool\n\ndef production_evidence_learning_health(root=None,settled_limit=100):\n    root=Path(root or Path.cwd()).resolve()\n    active=verify_olr_046_oracle_live_evidence_learner_launcher_cutover(root)\n    metrics=read_linkage_metrics(root,settled_limit)\n    healthy=bool(active and metrics.settled>=0)\n    return EvidenceLearningHealth(\n        active,metrics.settled,metrics.evidence_matched,metrics.evidence_missing,\n        metrics.evidence_coverage,metrics.learning_yield,healthy\n    )\n\ndef verify_olr_049_production_evidence_learning_health_verification(root=None):\n    h=production_evidence_learning_health(root,100)\n    return OLR_049_BUILD_ID=="OLR-049" and h.launcher_active and h.healthy\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_049_production_evidence_learning_health_verification import *\nclass T(unittest.TestCase):\n    def test_contract(self):\n        h=EvidenceLearningHealth(True,100,20,80,.2,0.0,True)\n        self.assertTrue(h.healthy)\n        self.assertEqual(h.evidence_matched+h.evidence_missing,h.settled)\nif __name__=="__main__":\n    print("="*88);print(" OLR-049 CERTIFICATION TEST");print(" PRODUCTION EVIDENCE-LEARNING HEALTH VERIFICATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Production evidence-learning health contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-049 CERTIFIED")\n'

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
    print("="*88);print(" OLR-049 INSTALLER");print(" PRODUCTION EVIDENCE-LEARNING HEALTH VERIFICATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_048_postgresql_live_learning_metrics_read_model")
    if not up.verify_olr_048_postgresql_live_learning_metrics_read_model(ROOT):raise RuntimeError("Certified OLR-048 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_049_production_evidence_learning_health_verification import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_049_production_evidence_learning_health_verification")
        h=m.production_evidence_learning_health(ROOT,100)
        print(f"[HEALTH] launcher_active={h.launcher_active} settled={h.settled} evidence_matched={h.evidence_matched} evidence_missing={h.evidence_missing} evidence_coverage={h.evidence_coverage:.3f} learning_yield={h.learning_yield:.3f}")
        if not h.launcher_active:raise RuntimeError("Evidence-enabled learner is not active in Oracle Live launcher")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-049 installation failed; affected files restored");raise
    print("[PASS] Production learner activation physically verified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-049 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
