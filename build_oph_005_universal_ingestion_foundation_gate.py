from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_005_universal_ingestion_foundation_gate.py"; TEST=ROOT/"test_oph_005_universal_ingestion_foundation_gate.py"; INIT=PKG/"__init__.py"
MODULE='import importlib\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass UniversalIngestionFoundationReport:\n    certified_start:str; certified_end:str; single_writer_contract:bool; priority_queue_contract:bool; durable_state_contract:bool; universal_adapter_gateway:bool; direct_adapter_canonical_write_authority:bool=False; terminal_dependency:bool=False; execution_authority:bool=False\n\ndef verify_oph_005_universal_ingestion_foundation_gate():\n    checks=(("oph_001_single_canonical_writer_service","verify_oph_001_single_canonical_writer_service"),("oph_002_priority_observation_ingestion_queue","verify_oph_002_priority_observation_ingestion_queue"),("oph_003_shared_durable_state_persistence_runtime","verify_oph_003_shared_durable_state_persistence_runtime"),("oph_004_universal_adapter_admission_gateway","verify_oph_004_universal_adapter_admission_gateway"))\n    return all(getattr(importlib.import_module("qseries_v2.oracle_production_hardening."+m),f)() for m,f in checks)\n\ndef foundation_report():\n    if not verify_oph_005_universal_ingestion_foundation_gate(): raise RuntimeError("OPH-001 through OPH-005 verification failed")\n    return UniversalIngestionFoundationReport("OPH-001","OPH-005",True,True,True,True,False,False,False)\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_005_universal_ingestion_foundation_gate import verify_oph_005_universal_ingestion_foundation_gate\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_005_universal_ingestion_foundation_gate())\nif __name__=="__main__":\n    print("="*80); print(" OPH-005 CERTIFICATION TEST"); print(" UNIVERSAL INGESTION FOUNDATION GATE"); print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPH-005 certified"); print("[DONE] OPH-005 CERTIFIED")\n'
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*80); print(" OPH-005 INSTALLER"); print(" UNIVERSAL INGESTION FOUNDATION GATE"); print("="*80); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_004_universal_adapter_admission_gateway")
    if up.verify_oph_004_universal_adapter_admission_gateway() is not True: raise RuntimeError("OPH-004 verification failed")
    print("[PASS] Certified OPH-004 upstream boundary verified")
    affected=(MOD,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE); write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .oph_005_universal_ingestion_foundation_gate import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPH-005 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[DONE] OPH-005 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
