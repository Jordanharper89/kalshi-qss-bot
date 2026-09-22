from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_011_universal_coverage_scheduler.py"; TEST=ROOT/"test_opc_011_universal_coverage_scheduler.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass CoverageWorkItem:\n    ticker:str; reason:str="UNCOVERED"; read_only:bool=True; execution_allowed:bool=False\ndef schedule_uncovered(open_tickers,covered_tickers,limit=100):\n    covered=set(map(str,covered_tickers)); missing=sorted(set(map(str,open_tickers))-covered)\n    return tuple(CoverageWorkItem(x) for x in missing[:int(limit)])\ndef verify_opc_011_universal_coverage_scheduler():\n    x=schedule_uncovered(("B","A","C"),("B",),2)\n    return tuple(i.ticker for i in x)==("A","C") and all(not i.execution_allowed for i in x)\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_011_universal_coverage_scheduler import verify_opc_011_universal_coverage_scheduler\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_011_universal_coverage_scheduler())\nif __name__=="__main__":\n    print("="*72); print(" OPC-011 CERTIFICATION TEST"); print(" UNIVERSAL COVERAGE SCHEDULER"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-011 certified"); print("[DONE] OPC-011 CERTIFIED")\n'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*72); print(" OPC-011 INSTALLER"); print(" UNIVERSAL COVERAGE SCHEDULER"); print("="*72); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model")
    if up.verify_opc_003_canonical_observation_coverage_read_model() is not True: raise RuntimeError("Corrected OPC-003 verification failed")
    print("[PASS] Corrected OPC-003 coverage boundary verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .opc_011_universal_coverage_scheduler import *"
        if ex not in cur: write(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPC-011 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] Updated:",INIT.relative_to(ROOT)); print("[DONE] OPC-011 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
