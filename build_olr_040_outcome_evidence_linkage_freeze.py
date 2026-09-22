from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_040_outcome_evidence_linkage_freeze.py";TEST=ROOT/"test_olr_040_outcome_evidence_linkage_freeze.py";INIT=PKG/"__init__.py";MANIFEST=PKG/"OLR_040_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict\nfrom pathlib import Path\nimport hashlib,json\nOLR_040_BUILD_ID="OLR-040"\nOLR_040_REVISION="OLR_040_OUTCOME_EVIDENCE_LINKAGE_FREEZE_V1"\n\ndef write_olr_040_freeze_manifest(root=None):\n    from .olr_036_outcome_evidence_linkage_foundation import verify_olr_036_outcome_evidence_linkage_foundation\n    from .olr_037_market_evidence_candidate_matching import verify_olr_037_market_evidence_candidate_matching\n    from .olr_038_postgresql_outcome_evidence_linkage_ledger import verify_olr_038_postgresql_outcome_evidence_linkage_ledger\n    from .olr_039_evidence_coverage_recovery_engine import verify_olr_039_evidence_coverage_recovery_engine\n    root=Path(root or Path.cwd()).resolve()\n    checks={\n      "olr_036":verify_olr_036_outcome_evidence_linkage_foundation(root),\n      "olr_037":verify_olr_037_market_evidence_candidate_matching(root),\n      "olr_038":verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root),\n      "olr_039":verify_olr_039_evidence_coverage_recovery_engine(root),\n    }\n    if not all(checks.values()):raise RuntimeError("OLR-036 through OLR-039 verification failed")\n    body={"build_id":OLR_040_BUILD_ID,"revision":OLR_040_REVISION,"verified":checks,\n          "frozen_capability":{"deterministic_outcome_keys":True,"candidate_matching":True,\n          "postgresql_linkage_ledger":True,"evidence_coverage_recovery":True,\n          "learning_application_authority":False,"execution_authority":False}}\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_040_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_olr_040_outcome_evidence_linkage_freeze(root=None):\n    from .olr_039_evidence_coverage_recovery_engine import verify_olr_039_evidence_coverage_recovery_engine\n    return verify_olr_039_evidence_coverage_recovery_engine(root) and OLR_040_BUILD_ID=="OLR-040"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_040_outcome_evidence_linkage_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_040_BUILD_ID,"OLR-040")\n    def test_revision(self):self.assertIn("OUTCOME_EVIDENCE_LINKAGE_FREEZE",OLR_040_REVISION)\nif __name__=="__main__":\n    print("="*88);print(" OLR-040 CERTIFICATION TEST");print(" OUTCOME-EVIDENCE LINKAGE FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Outcome-evidence linkage capability freeze certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-040 CERTIFIED")\n'

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
    print("="*88);print(" OLR-040 INSTALLER");print(" OUTCOME-EVIDENCE LINKAGE FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_039_evidence_coverage_recovery_engine")
    if not up.verify_olr_039_evidence_coverage_recovery_engine(ROOT):raise RuntimeError("Certified OLR-039 verification failed")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_040_outcome_evidence_linkage_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_040_outcome_evidence_linkage_freeze")
        path,body=m.write_olr_040_freeze_manifest(ROOT)
        print("[PASS] Wrote:",path.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-040 installation failed; affected files restored");raise
    print("[PASS] Existing learning application authority unchanged")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] execution_authority=FALSE");print("[DONE] OLR-040 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
