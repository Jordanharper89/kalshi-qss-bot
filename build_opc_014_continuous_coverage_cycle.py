from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_014_continuous_coverage_cycle.py"; TEST=ROOT/"test_opc_014_continuous_coverage_cycle.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom .opc_011_universal_coverage_scheduler import schedule_uncovered\nfrom .opc_012_coverage_priority_engine import prioritize_coverage\n@dataclass(frozen=True)\nclass ContinuousCoveragePlan:\n    open_count:int; covered_count:int; selected_tickers:tuple; bounded_limit:int; read_only:bool=True; execution_allowed:bool=False\ndef plan_continuous_coverage_cycle(open_tickers,covered_tickers,facts=None,limit=100):\n    work=schedule_uncovered(open_tickers,covered_tickers,max(int(limit)*4,int(limit)))\n    ranked=prioritize_coverage(work,facts)\n    return ContinuousCoveragePlan(len(set(open_tickers)),len(set(covered_tickers)),tuple(x.ticker for x in ranked[:int(limit)]),int(limit))\ndef verify_opc_014_continuous_coverage_cycle():\n    x=plan_continuous_coverage_cycle(("A","B","C"),("A",),{"C":{"active":True}},2)\n    return x.selected_tickers==("C","B") and not x.execution_allowed\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_014_continuous_coverage_cycle import verify_opc_014_continuous_coverage_cycle\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_014_continuous_coverage_cycle())\nif __name__=="__main__":\n    print("="*72); print(" OPC-014 CERTIFICATION TEST"); print(" CONTINUOUS COVERAGE CYCLE"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-014 certified"); print("[DONE] OPC-014 CERTIFIED")\n'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*72); print(" OPC-014 INSTALLER"); print(" CONTINUOUS COVERAGE CYCLE"); print("="*72); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_013_coverage_freshness_refresh_policy")
    if up.verify_opc_013_coverage_freshness_refresh_policy() is not True: raise RuntimeError("OPC-013 verification failed")
    print("[PASS] Certified OPC-013 upstream boundary verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .opc_014_continuous_coverage_cycle import *"
        if ex not in cur: write(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPC-014 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] Updated:",INIT.relative_to(ROOT)); print("[DONE] OPC-014 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
