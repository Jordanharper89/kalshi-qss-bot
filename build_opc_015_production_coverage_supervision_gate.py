from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_015_production_coverage_supervision_gate.py"; TEST=ROOT/"test_opc_015_production_coverage_supervision_gate.py"; INIT=PKG/"__init__.py"
MODULE='import importlib\nEXECUTION_AUTHORITY=False\nTERMINAL_DEPENDENCY=False\ndef verify_opc_015_production_coverage_supervision_gate():\n    checks=(("opc_011_universal_coverage_scheduler","verify_opc_011_universal_coverage_scheduler"),("opc_012_coverage_priority_engine","verify_opc_012_coverage_priority_engine"),("opc_013_coverage_freshness_refresh_policy","verify_opc_013_coverage_freshness_refresh_policy"),("opc_014_continuous_coverage_cycle","verify_opc_014_continuous_coverage_cycle"))\n    return all(getattr(importlib.import_module("qseries_v2.oracle_pre_settlement_coverage."+m),f)() for m,f in checks) and not EXECUTION_AUTHORITY and not TERMINAL_DEPENDENCY\ndef production_coverage_supervision_report():\n    if not verify_opc_015_production_coverage_supervision_gate(): raise RuntimeError("OPC slice verification failed")\n    return {"certified_start":"OPC-011","certified_end":"OPC-015","continuous_coverage_ready":True,"execution_authority":False,"terminal_dependency":False}\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_015_production_coverage_supervision_gate import verify_opc_015_production_coverage_supervision_gate\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_015_production_coverage_supervision_gate())\nif __name__=="__main__":\n    print("="*72); print(" OPC-015 CERTIFICATION TEST"); print(" PRODUCTION COVERAGE SUPERVISION GATE"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-015 certified"); print("[DONE] OPC-015 CERTIFIED")\n'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*72); print(" OPC-015 INSTALLER"); print(" PRODUCTION COVERAGE SUPERVISION GATE"); print("="*72); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_014_continuous_coverage_cycle")
    if up.verify_opc_014_continuous_coverage_cycle() is not True: raise RuntimeError("OPC-014 verification failed")
    print("[PASS] Certified OPC-014 upstream boundary verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .opc_015_production_coverage_supervision_gate import *"
        if ex not in cur: write(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPC-015 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] Updated:",INIT.relative_to(ROOT)); print("[DONE] OPC-015 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
