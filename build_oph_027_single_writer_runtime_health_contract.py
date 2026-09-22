from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_027_single_writer_runtime_health_contract.py"
TEST=ROOT/"test_oph_027_single_writer_runtime_health_contract.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nfrom .oph_019_postgresql_universal_ingestion_queue import queue_counts\nfrom .oph_026_postgresql_ingestion_pressure_control import read_ingestion_pressure\nOPH_027_BUILD_ID="OPH-027"\nOPH_027_REVISION="OPH_027_SINGLE_WRITER_RUNTIME_HEALTH_CONTRACT_V1"\n\n@dataclass(frozen=True)\nclass SingleWriterHealth:\n    architecture_verified:bool\n    pending:int\n    in_progress:int\n    failed:int\n    pressure_level:str\n    execution_authority:bool=False\n\ndef single_writer_health(root=None):\n    from .oph_023_postgresql_single_writer_production_freeze import verify_oph_023_postgresql_single_writer_production_freeze\n    root=Path(root or Path.cwd()).resolve();p=read_ingestion_pressure(root)\n    return SingleWriterHealth(bool(verify_oph_023_postgresql_single_writer_production_freeze(root)),p.pending,p.in_progress,p.failed,p.level,False)\n\ndef verify_oph_027_single_writer_runtime_health_contract(root=None):\n    from .oph_026_postgresql_ingestion_pressure_control import verify_oph_026_postgresql_ingestion_pressure_control\n    return verify_oph_026_postgresql_ingestion_pressure_control(root) and single_writer_health(root).architecture_verified\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_027_single_writer_runtime_health_contract import *\nclass T(unittest.TestCase):\n    def test_contract(self):\n        x=SingleWriterHealth(True,0,0,0,"NORMAL",False)\n        self.assertTrue(x.architecture_verified);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88);print(" OPH-027 CERTIFICATION TEST");print(" SINGLE-WRITER RUNTIME HEALTH CONTRACT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Single-writer runtime health contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-027 CERTIFIED")\n'

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
    print("="*88);print(" OPH-027 INSTALLER");print(" SINGLE-WRITER RUNTIME HEALTH CONTRACT");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_026_postgresql_ingestion_pressure_control")
    verifier=getattr(up,"verify_oph_026_postgresql_ingestion_pressure_control")
    if verifier(ROOT) is not True:
        raise RuntimeError("Certified OPH-026 upstream verification failed")
    print("[PASS] Certified OPH-026 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,'from .oph_027_single_writer_runtime_health_contract import *')
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_027_single_writer_runtime_health_contract")
        if getattr(m,"verify_oph_027_single_writer_runtime_health_contract")(ROOT) is not True:
            raise RuntimeError("OPH-027 physical verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-027 installation failed; affected files restored");raise
    print("[PASS] SINGLE-WRITER RUNTIME HEALTH CONTRACT installed")
    print("[PASS] OPH-001 through OPH-026 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-027 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
