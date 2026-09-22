from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_012_coverage_priority_engine.py"; TEST=ROOT/"test_opc_012_coverage_priority_engine.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass PrioritizedCoverageMarket:\n    ticker:str; score:int; reason_codes:tuple; read_only:bool=True; execution_allowed:bool=False\ndef prioritize_coverage(items,facts=None):\n    facts=facts or {}; out=[]\n    for item in items:\n        t=str(getattr(item,"ticker",item)); f=facts.get(t,{})\n        s=100; r=["UNCOVERED"]\n        if f.get("active"): s+=40; r.append("ACTIVE")\n        if f.get("volume",0)>0: s+=20; r.append("HAS_VOLUME")\n        if f.get("close_soon"): s+=30; r.append("CLOSE_SOON")\n        out.append(PrioritizedCoverageMarket(t,s,tuple(r)))\n    return tuple(sorted(out,key=lambda x:(-x.score,x.ticker)))\ndef verify_opc_012_coverage_priority_engine():\n    x=prioritize_coverage(("A","B"),{"B":{"active":True}})\n    return x[0].ticker=="B" and x[0].score>x[1].score\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_012_coverage_priority_engine import verify_opc_012_coverage_priority_engine\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_012_coverage_priority_engine())\nif __name__=="__main__":\n    print("="*72); print(" OPC-012 CERTIFICATION TEST"); print(" COVERAGE PRIORITY ENGINE"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-012 certified"); print("[DONE] OPC-012 CERTIFIED")\n'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*72); print(" OPC-012 INSTALLER"); print(" COVERAGE PRIORITY ENGINE"); print("="*72); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_011_universal_coverage_scheduler")
    if up.verify_opc_011_universal_coverage_scheduler() is not True: raise RuntimeError("OPC-011 verification failed")
    print("[PASS] Certified OPC-011 upstream boundary verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .opc_012_coverage_priority_engine import *"
        if ex not in cur: write(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPC-012 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] Updated:",INIT.relative_to(ROOT)); print("[DONE] OPC-012 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
