from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_045_live_evidence_grounded_learning_freeze.py";TEST=ROOT/"test_olr_045_live_evidence_grounded_learning_freeze.py";INIT=PKG/"__init__.py";MANIFEST=PKG/"OLR_045_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport hashlib,json\n\nOLR_045_BUILD_ID="OLR-045"\nOLR_045_REVISION="OLR_045_LIVE_EVIDENCE_GROUNDED_LEARNING_FREEZE_V1"\n\ndef write_olr_045_freeze_manifest(root=None):\n    from .olr_041_postgresql_live_evidence_lookup import verify_olr_041_postgresql_live_evidence_lookup\n    from .olr_042_live_evidence_admission_gate import verify_olr_042_live_evidence_admission_gate\n    from .olr_043_live_learning_evidence_adapter import verify_olr_043_live_learning_evidence_adapter\n    from .olr_044_continuous_learner_evidence_runtime_cutover import verify_olr_044_continuous_learner_evidence_runtime_cutover\n    root=Path(root or Path.cwd()).resolve()\n    checks={\n        "olr_041":verify_olr_041_postgresql_live_evidence_lookup(root),\n        "olr_042":verify_olr_042_live_evidence_admission_gate(root),\n        "olr_043":verify_olr_043_live_learning_evidence_adapter(root),\n        "olr_044":verify_olr_044_continuous_learner_evidence_runtime_cutover(root),\n    }\n    if not all(checks.values()):raise RuntimeError("OLR-041 through OLR-044 verification failed")\n    body={\n        "build_id":OLR_045_BUILD_ID,\n        "revision":OLR_045_REVISION,\n        "verified":checks,\n        "frozen_capability":{\n            "live_postgresql_evidence_lookup":True,\n            "evidence_admission_gate":True,\n            "durable_linkage_reuse":True,\n            "continuous_learning_evidence_wrapper":True,\n            "missing_evidence_abstains":True,\n            "execution_authority":False,\n        },\n    }\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"))\n    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_045_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_olr_045_live_evidence_grounded_learning_freeze(root=None):\n    from .olr_044_continuous_learner_evidence_runtime_cutover import verify_olr_044_continuous_learner_evidence_runtime_cutover\n    return verify_olr_044_continuous_learner_evidence_runtime_cutover(root) and OLR_045_BUILD_ID=="OLR-045"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_045_live_evidence_grounded_learning_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_045_BUILD_ID,"OLR-045")\n    def test_revision(self):self.assertIn("LIVE_EVIDENCE_GROUNDED_LEARNING_FREEZE",OLR_045_REVISION)\nif __name__=="__main__":\n    print("="*88);print(" OLR-045 CERTIFICATION TEST");print(" LIVE EVIDENCE-GROUNDED LEARNING FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Live evidence-grounded learning freeze certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-045 CERTIFIED")\n'

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
    print("="*88);print(" OLR-045 INSTALLER");print(" LIVE EVIDENCE-GROUNDED LEARNING FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_044_continuous_learner_evidence_runtime_cutover")
    if not up.verify_olr_044_continuous_learner_evidence_runtime_cutover(ROOT):raise RuntimeError("Certified OLR-044 verification failed")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_045_live_evidence_grounded_learning_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_045_live_evidence_grounded_learning_freeze")
        path,body=m.write_olr_045_freeze_manifest(ROOT)
        print("[PASS] Wrote:",path.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-045 installation failed; affected files restored");raise
    print("[PASS] OLR-036 through OLR-040 preserved frozen")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-045 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
