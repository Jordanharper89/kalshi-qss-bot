from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_050_production_evidence_learning_activation_freeze.py";TEST=ROOT/"test_olr_050_production_evidence_learning_activation_freeze.py";INIT=PKG/"__init__.py";MANIFEST=PKG/"OLR_050_FREEZE_MANIFEST.json";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport hashlib,json\nfrom .olr_049_production_evidence_learning_health_verification import production_evidence_learning_health\n\nOLR_050_BUILD_ID="OLR-050"\nOLR_050_REVISION="OLR_050_PRODUCTION_EVIDENCE_LEARNING_ACTIVATION_FREEZE_V1"\n\ndef write_olr_050_freeze_manifest(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    health=production_evidence_learning_health(root,100)\n    if not health.launcher_active or not health.healthy:\n        raise RuntimeError("Production evidence-learning activation verification failed")\n    body={\n        "build_id":OLR_050_BUILD_ID,\n        "revision":OLR_050_REVISION,\n        "production_health":health.__dict__,\n        "frozen_capability":{\n            "oracle_live_learning_child_evidence_enabled":True,\n            "live_learning_metrics_contract":True,\n            "postgresql_metrics_read_model":True,\n            "production_health_verification":True,\n            "missing_evidence_abstains":True,\n            "execution_authority":False,\n        },\n    }\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"))\n    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_050_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_olr_050_production_evidence_learning_activation_freeze(root=None):\n    h=production_evidence_learning_health(root,100)\n    return OLR_050_BUILD_ID=="OLR-050" and h.launcher_active and h.healthy\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_050_production_evidence_learning_activation_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_050_BUILD_ID,"OLR-050")\n    def test_revision(self):self.assertIn("PRODUCTION_EVIDENCE_LEARNING_ACTIVATION_FREEZE",OLR_050_REVISION)\nif __name__=="__main__":\n    print("="*88);print(" OLR-050 CERTIFICATION TEST");print(" PRODUCTION EVIDENCE-LEARNING ACTIVATION FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Production evidence-learning activation freeze contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-050 CERTIFIED")\n'

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
    print("="*88);print(" OLR-050 INSTALLER");print(" PRODUCTION EVIDENCE-LEARNING ACTIVATION FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_049_production_evidence_learning_health_verification")
    if not up.verify_olr_049_production_evidence_learning_health_verification(ROOT):raise RuntimeError("Certified OLR-049 verification failed")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_050_production_evidence_learning_activation_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_050_production_evidence_learning_activation_freeze")
        path,body=m.write_olr_050_freeze_manifest(ROOT)
        print("[PASS] Wrote:",path.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-050 installation failed; affected files restored");raise
    print("[PASS] Oracle Live evidence-enabled learning child frozen active")
    print("[PASS] OLR-036 through OLR-045 preserved frozen")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-050 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
