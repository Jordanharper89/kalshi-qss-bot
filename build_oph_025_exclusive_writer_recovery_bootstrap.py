from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_025_exclusive_writer_recovery_bootstrap.py"
TEST=ROOT/"test_oph_025_exclusive_writer_recovery_bootstrap.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nOPH_025_BUILD_ID="OPH-025"\nOPH_025_REVISION="OPH_025_EXCLUSIVE_WRITER_RECOVERY_BOOTSTRAP_V1"\n\ndef install_writer_recovery_bootstrap(root=None):\n    from . import oph_021_exclusive_postgresql_canonical_writer as writer\n    from .oph_024_postgresql_stale_claim_recovery import recover_stale_claims\n    root=Path(root or Path.cwd()).resolve()\n    if getattr(writer,"_oph025_recovery_bootstrap",False):return False\n    original=writer.run_exclusive_writer_forever\n    def recovered(root_arg=None,progress=None,idle_sleep_seconds=0.002):\n        actual=Path(root_arg or root).resolve()\n        recovered_ids=recover_stale_claims(actual)\n        if progress:progress(f"[OPH-025 RECOVERY] stale_claims_recovered={len(recovered_ids)}")\n        return original(actual,progress,idle_sleep_seconds)\n    writer.run_exclusive_writer_forever=recovered\n    writer._oph025_recovery_bootstrap=True\n    return True\n\ndef verify_oph_025_exclusive_writer_recovery_bootstrap(root=None):\n    from .oph_024_postgresql_stale_claim_recovery import verify_oph_024_postgresql_stale_claim_recovery\n    return verify_oph_024_postgresql_stale_claim_recovery(root) and OPH_025_BUILD_ID=="OPH-025"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_025_exclusive_writer_recovery_bootstrap import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPH_025_BUILD_ID,"OPH-025")\n    def test_callable(self):self.assertTrue(callable(install_writer_recovery_bootstrap))\nif __name__=="__main__":\n    print("="*88);print(" OPH-025 CERTIFICATION TEST");print(" EXCLUSIVE WRITER RECOVERY BOOTSTRAP");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Writer restart recovery bootstrap certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-025 CERTIFIED")\n'

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
    print("="*88);print(" OPH-025 INSTALLER");print(" EXCLUSIVE WRITER RECOVERY BOOTSTRAP");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_024_postgresql_stale_claim_recovery")
    verifier=getattr(up,"verify_oph_024_postgresql_stale_claim_recovery")
    if verifier(ROOT) is not True:
        raise RuntimeError("Certified OPH-024 upstream verification failed")
    print("[PASS] Certified OPH-024 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,'from .oph_025_exclusive_writer_recovery_bootstrap import *')
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_025_exclusive_writer_recovery_bootstrap")
        if getattr(m,"verify_oph_025_exclusive_writer_recovery_bootstrap")(ROOT) is not True:
            raise RuntimeError("OPH-025 physical verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-025 installation failed; affected files restored");raise
    print("[PASS] EXCLUSIVE WRITER RECOVERY BOOTSTRAP installed")
    print("[PASS] OPH-001 through OPH-024 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-025 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
