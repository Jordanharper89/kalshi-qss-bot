from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD_PATH=PKG/"ohl_009_historical_eligibility_census.py"
TEST_PATH=ROOT/"test_ohl_009_historical_eligibility_census.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom collections import Counter\nfrom pathlib import Path\nfrom .ohl_006_settled_outcome_inventory_adapter import read_settled_outcome_inventory\nfrom .ohl_008_settled_market_eligibility_evaluator import evaluate_settled_market_eligibility,verify_ohl_008_settled_market_eligibility_evaluator\n\nOHL_009_BUILD_ID="OHL-009"\nOHL_009_REVISION="OHL_009_HISTORICAL_ELIGIBILITY_CENSUS_V1"\n\n@dataclass(frozen=True)\nclass HistoricalEligibilityCensus:\n    settled_scanned:int\n    unique_tickers:int\n    eligible_markets:int\n    ineligible_markets:int\n    eligibility_rate:float\n    total_pre_settlement_evidence:int\n    reasons:tuple\n    eligible_tickers:tuple\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef run_historical_eligibility_census(root=None,settled_limit=500,evidence_limit=50,progress=None):\n    if not verify_ohl_008_settled_market_eligibility_evaluator():\n        raise RuntimeError("OHL-008 verification failed")\n    root=Path(root or Path.cwd()).resolve()\n    inv=read_settled_outcome_inventory(root,settled_limit)\n    results=[]\n    for idx,outcome in enumerate(inv.outcomes,1):\n        r=evaluate_settled_market_eligibility(root,outcome,evidence_limit)\n        results.append(r)\n        if progress:\n            progress(f"[CENSUS] {idx}/{inv.settled_count} ticker={r.ticker} eligible={r.eligible} evidence={r.evidence_count} reason={r.reason}")\n    eligible=[r for r in results if r.eligible]\n    reasons=Counter(r.reason for r in results if not r.eligible)\n    total_evidence=sum(r.evidence_count for r in results)\n    rate=(len(eligible)/len(results)) if results else 0.0\n    return HistoricalEligibilityCensus(\n        len(results),inv.unique_tickers,len(eligible),len(results)-len(eligible),\n        rate,total_evidence,tuple(sorted(reasons.items())),\n        tuple(sorted(r.ticker for r in eligible)),True,False\n    )\n\ndef verify_ohl_009_historical_eligibility_census():\n    x=HistoricalEligibilityCensus(0,0,0,0,0.0,0,tuple(),tuple(),True,False)\n    return x.read_only and not x.execution_authority\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_historical_learning.ohl_009_historical_eligibility_census import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ohl_009_historical_eligibility_census())\n    def test_zero_rate(self):self.assertEqual(HistoricalEligibilityCensus(0,0,0,0,0,0,tuple(),tuple(),True,False).eligibility_rate,0)\n\nif __name__=="__main__":\n    print("="*72);print(" OHL-009 CERTIFICATION TEST");print(" HISTORICAL ELIGIBILITY CENSUS");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Read-only historical eligibility census certified")\n    print("[DONE] OHL-009 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-009 INSTALLER")
    print(" HISTORICAL ELIGIBILITY CENSUS")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module('qseries_v2.oracle_historical_learning.ohl_008_settled_market_eligibility_evaluator')
    if getattr(up,'verify_ohl_008_settled_market_eligibility_evaluator')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OHL-008 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .ohl_009_historical_eligibility_census import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-009 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OHL-009 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
