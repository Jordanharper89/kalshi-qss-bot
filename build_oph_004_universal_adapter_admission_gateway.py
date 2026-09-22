from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_004_universal_adapter_admission_gateway.py"; TEST=ROOT/"test_oph_004_universal_adapter_admission_gateway.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom .oph_001_single_canonical_writer_service import SingleCanonicalWriterService\nfrom .oph_002_priority_observation_ingestion_queue import admit_observations\n\n@dataclass(frozen=True)\nclass AdapterAdmissionReceipt:\n    adapter_id:str; lane:str; priority:int; observation_count:int; writer_sequence:int; direct_postgresql_write_authority:bool=False; execution_authority:bool=False\n\nclass UniversalAdapterAdmissionGateway:\n    def __init__(self,writer_service=None): self.writer_service=writer_service or SingleCanonicalWriterService()\n    def submit(self,adapter_id,lane,observations):\n        a=admit_observations(adapter_id,lane,observations)\n        e=self.writer_service.submit(a.adapter_id,a.observations,a.priority)\n        return AdapterAdmissionReceipt(a.adapter_id,a.lane,a.priority,len(a.observations),e.admitted_sequence,False,False)\n\ndef verify_oph_004_universal_adapter_admission_gateway():\n    g=UniversalAdapterAdmissionGateway()\n    xs=[g.submit("kalshi","FAST_LANE",("a",)),g.submit("coinbase","LIVE_ADAPTER",("b",)),g.submit("polymarket","NORMAL",("c",)),g.submit("solana","NORMAL",("d",))]\n    return xs[0].priority>xs[1].priority>xs[2].priority and all(not x.direct_postgresql_write_authority and not x.execution_authority for x in xs)\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_004_universal_adapter_admission_gateway import verify_oph_004_universal_adapter_admission_gateway\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_004_universal_adapter_admission_gateway())\nif __name__=="__main__":\n    print("="*80); print(" OPH-004 CERTIFICATION TEST"); print(" UNIVERSAL ADAPTER ADMISSION GATEWAY"); print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPH-004 certified"); print("[DONE] OPH-004 CERTIFIED")\n'
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*80); print(" OPH-004 INSTALLER"); print(" UNIVERSAL ADAPTER ADMISSION GATEWAY"); print("="*80); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_003_shared_durable_state_persistence_runtime")
    if up.verify_oph_003_shared_durable_state_persistence_runtime() is not True: raise RuntimeError("OPH-003 verification failed")
    print("[PASS] Certified OPH-003 upstream boundary verified")
    affected=(MOD,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE); write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .oph_004_universal_adapter_admission_gateway import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPH-004 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[DONE] OPH-004 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
