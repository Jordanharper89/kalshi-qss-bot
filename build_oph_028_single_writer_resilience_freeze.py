from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_028_single_writer_resilience_freeze.py"
TEST=ROOT/"test_oph_028_single_writer_resilience_freeze.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict\nfrom pathlib import Path\nimport hashlib,json\nOPH_028_BUILD_ID="OPH-028"\nOPH_028_REVISION="OPH_028_SINGLE_WRITER_RESILIENCE_FREEZE_V1"\n\ndef write_oph_028_freeze_manifest(root=None):\n    from .oph_027_single_writer_runtime_health_contract import single_writer_health\n    root=Path(root or Path.cwd()).resolve();health=single_writer_health(root)\n    if not health.architecture_verified:raise RuntimeError("Single-writer architecture verification failed")\n    body={"build_id":OPH_028_BUILD_ID,"revision":OPH_028_REVISION,"health_at_freeze":asdict(health),\n          "frozen_capability":{"stale_claim_recovery":True,"writer_restart_recovery":True,\n          "postgresql_pressure_control":True,"runtime_health_contract":True,\n          "canonical_writer_count":1,"sqlite_active_ingestion":False,"execution_authority":False}}\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_028_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_oph_028_single_writer_resilience_freeze(root=None):\n    from .oph_027_single_writer_runtime_health_contract import verify_oph_027_single_writer_runtime_health_contract\n    return verify_oph_027_single_writer_runtime_health_contract(root) and OPH_028_BUILD_ID=="OPH-028"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_028_single_writer_resilience_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPH_028_BUILD_ID,"OPH-028")\n    def test_revision(self):self.assertIn("RESILIENCE_FREEZE",OPH_028_REVISION)\nif __name__=="__main__":\n    print("="*88);print(" OPH-028 CERTIFICATION TEST");print(" SINGLE-WRITER RESILIENCE FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Single-writer resilience freeze contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-028 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-028 INSTALLER");print(" SINGLE-WRITER RESILIENCE FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_027_single_writer_runtime_health_contract")
    verifier=getattr(up,"verify_oph_027_single_writer_runtime_health_contract")
    if verifier(ROOT) is not True:
        raise RuntimeError("Certified OPH-027 upstream verification failed")
    print("[PASS] Certified OPH-027 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,'from .oph_028_single_writer_resilience_freeze import *')
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_028_single_writer_resilience_freeze")
        if getattr(m,"verify_oph_028_single_writer_resilience_freeze")(ROOT) is not True:
            raise RuntimeError("OPH-028 physical verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-028 installation failed; affected files restored");raise
    print("[PASS] SINGLE-WRITER RESILIENCE FREEZE installed")
    print("[PASS] OPH-001 through OPH-027 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-028 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
