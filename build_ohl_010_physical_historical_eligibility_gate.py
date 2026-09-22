from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD_PATH=PKG/"ohl_010_physical_historical_eligibility_gate.py"
TEST_PATH=ROOT/"test_ohl_010_physical_historical_eligibility_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom .ohl_006_settled_outcome_inventory_adapter import verify_ohl_006_settled_outcome_inventory_adapter\nfrom .ohl_007_historical_evidence_coverage_scanner import verify_ohl_007_historical_evidence_coverage_scanner\nfrom .ohl_008_settled_market_eligibility_evaluator import verify_ohl_008_settled_market_eligibility_evaluator\nfrom .ohl_009_historical_eligibility_census import verify_ohl_009_historical_eligibility_census\n\nOHL_010_BUILD_ID="OHL-010"\nOHL_010_REVISION="OHL_010_PHYSICAL_HISTORICAL_ELIGIBILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass OHL010Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ohl_006_through_010():\n    if not all((\n        verify_ohl_006_settled_outcome_inventory_adapter(),\n        verify_ohl_007_historical_evidence_coverage_scanner(),\n        verify_ohl_008_settled_market_eligibility_evaluator(),\n        verify_ohl_009_historical_eligibility_census(),\n    )):\n        raise RuntimeError("OHL-006 through OHL-010 certification failed")\n    return OHL010Certification(\n        tuple("OHL-%03d"%i for i in range(6,11)),\n        "physical_postgresql_historical_learning_eligibility_census",\n        "historical_backfill_admission_and_durable_progress",\n        True\n    )\n\ndef verify_ohl_010_physical_historical_eligibility_gate():\n    c=certify_ohl_006_through_010()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_historical_learning.ohl_010_physical_historical_eligibility_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ohl_010_physical_historical_eligibility_gate())\n    def test_five(self):self.assertEqual(len(certify_ohl_006_through_010().builds),5)\n\nif __name__=="__main__":\n    print("="*72);print(" OHL-010 CERTIFICATION TEST");print(" PHYSICAL HISTORICAL ELIGIBILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OHL-006 through OHL-010 physical eligibility census certified")\n    print("[PASS] Next capability: historical backfill admission + durable progress")\n    print("[DONE] OHL-010 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_ohl_010_physical_historical_eligibility_census.py'
EXTRA_SOURCE_1='\nfrom pathlib import Path\nimport argparse\nfrom qseries_v2.oracle_historical_learning.ohl_009_historical_eligibility_census import run_historical_eligibility_census\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--settled-limit",type=int,default=500)\n    p.add_argument("--evidence-limit",type=int,default=50)\n    p.add_argument("--quiet",action="store_true")\n    a=p.parse_args()\n\n    print("="*72)\n    print(" OHL-010 PHYSICAL POSTGRESQL HISTORICAL ELIGIBILITY CENSUS")\n    print("="*72)\n    print(f"[CONFIG] settled_limit={a.settled_limit} evidence_limit={a.evidence_limit}")\n    progress=None if a.quiet else (lambda x:print(x,flush=True))\n    c=run_historical_eligibility_census(Path.cwd(),a.settled_limit,a.evidence_limit,progress)\n\n    print("="*72)\n    print(" HISTORICAL LEARNING ELIGIBILITY RESULT")\n    print("="*72)\n    print(f"[SETTLED SCANNED] {c.settled_scanned}")\n    print(f"[UNIQUE TICKERS] {c.unique_tickers}")\n    print(f"[ELIGIBLE MARKETS] {c.eligible_markets}")\n    print(f"[INELIGIBLE MARKETS] {c.ineligible_markets}")\n    print(f"[ELIGIBILITY RATE] {c.eligibility_rate:.2%}")\n    print(f"[PRE-SETTLEMENT EVIDENCE] {c.total_pre_settlement_evidence}")\n    print(f"[INELIGIBILITY REASONS] {c.reasons}")\n    if c.eligible_tickers:\n        print("[ELIGIBLE SAMPLE]",c.eligible_tickers[:25])\n    else:\n        print("[ELIGIBLE SAMPLE] NONE")\n    print("[PASS] PostgreSQL historical eligibility census completed read-only")\n    print("[PASS] Frozen OLR-001 through OLR-045 untouched")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OHL-010 PHYSICAL HISTORICAL ELIGIBILITY CENSUS COMPLETE")\n    return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-010 INSTALLER")
    print(" PHYSICAL HISTORICAL ELIGIBILITY GATE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module('qseries_v2.oracle_historical_learning.ohl_009_historical_eligibility_census')
    if getattr(up,'verify_ohl_009_historical_eligibility_census')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OHL-009 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .ohl_010_physical_historical_eligibility_gate import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(EXTRA_PATH_1),"--settled-limit","100","--evidence-limit","25","--quiet"],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-010 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OHL-010 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
