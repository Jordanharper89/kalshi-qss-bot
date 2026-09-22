from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_007_coverage_gap_snapshot_planner.py"; TEST=ROOT/"test_opc_007_coverage_gap_snapshot_planner.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass SnapshotPlan:\n    sampled_markets:int\n    already_covered:int\n    missing_markets:int\n    planned_tickers:tuple\n    bounded:bool=True\n    execution_authority:bool=False\ndef plan_missing_market_snapshots(open_markets,recent_canonical_tickers,max_markets=100):\n    max_markets=int(max_markets)\n    if max_markets<1 or max_markets>1000: raise ValueError("max_markets must be 1..1000")\n    recent={str(x) for x in recent_canonical_tickers}; planned=[]; total=covered=0\n    for row in open_markets:\n        if not isinstance(row,dict): continue\n        t=str(row.get("ticker") or "")\n        if not t: continue\n        total+=1\n        if t in recent: covered+=1\n        elif len(planned)<max_markets: planned.append(t)\n    return SnapshotPlan(total,covered,total-covered,tuple(planned),True,False)\ndef verify_opc_007_coverage_gap_snapshot_planner():\n    p=plan_missing_market_snapshots(({"ticker":"A"},{"ticker":"B"},{"ticker":"C"}),{"B"},2)\n    return p.sampled_markets==3 and p.already_covered==1 and p.planned_tickers==("A","C") and not p.execution_authority\n'; TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_007_coverage_gap_snapshot_planner import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_007_coverage_gap_snapshot_planner())\n    def test_bound(self):\n        with self.assertRaises(ValueError): plan_missing_market_snapshots((),set(),1001)\nif __name__=="__main__":\n    print("="*72);print(" OPC-007 CERTIFICATION TEST");print(" COVERAGE GAP SNAPSHOT PLANNER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Missing-market snapshot planning certified");print("[DONE] OPC-007 CERTIFIED")\n'
def w(p,t):
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    print("="*72);print(" OPC-007 INSTALLER");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer")
    if up.verify_opc_006_universal_market_snapshot_canonicalizer() is not True: raise RuntimeError("OPC-006 verification failed")
    print("[PASS] Certified OPC-006 upstream boundary verified")
    affected=(MOD,TEST,INIT); backups={x:(x.read_bytes() if x.exists() else None) for x in affected}
    try:
        w(MOD,MODULE_SOURCE); w(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; line="from .opc_007_coverage_gap_snapshot_planner import *"
        if line not in cur: w(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for x,old in backups.items():
            if old is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(old)
        print("[ROLLBACK] OPC-007 installation failed"); raise
    print("[DONE] OPC-007 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
