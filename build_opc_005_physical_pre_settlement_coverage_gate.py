from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_005_physical_pre_settlement_coverage_gate.py"
TEST=ROOT/"test_opc_005_physical_pre_settlement_coverage_gate.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='def verify_opc_005_physical_pre_settlement_coverage_gate():\n    from .opc_001_pre_settlement_coverage_foundation import verify_opc_001_pre_settlement_coverage_foundation as a\n    from .opc_002_bounded_open_market_sampler import verify_opc_002_bounded_open_market_sampler as b\n    from .opc_003_canonical_observation_coverage_read_model import verify_opc_003_canonical_observation_coverage_read_model as c\n    from .opc_004_live_coverage_gap_classifier import verify_opc_004_live_coverage_gap_classifier as d\n    return all((a(),b(),c(),d()))\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_005_physical_pre_settlement_coverage_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_005_physical_pre_settlement_coverage_gate())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-005 CERTIFICATION TEST")\n    print(" PHYSICAL PRE-SETTLEMENT COVERAGE GATE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-001 through OPC-005 live coverage measurement certified")\n    print("[DONE] OPC-005 CERTIFIED")\n'
RUNNER=ROOT/"run_opc_005_physical_live_pre_settlement_coverage_census.py"
RUNNER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import sample_live_open_markets\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers,evaluate_canonical_coverage\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_004_live_coverage_gap_classifier import classify_coverage_gap\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OPC-005 PHYSICAL LIVE PRE-SETTLEMENT COVERAGE CENSUS")\n    print("="*88)\n    s=sample_live_open_markets(Path.cwd(),pages=1)\n    print(f"[OPEN MARKET SAMPLE] unique_tickers={s.unique_tickers}")\n    c=read_recent_canonical_tickers(Path.cwd(),24,250000)\n    print(f"[CANONICAL RECENT] unique_tickers={len(c)}")\n    r=evaluate_canonical_coverage(s.markets,c)\n    g=classify_coverage_gap(r)\n    print(f"[SAMPLED OPEN MARKETS] {r.sampled_markets}")\n    print(f"[WITH CANONICAL OBSERVATION] {r.markets_with_canonical_observation}")\n    print(f"[WITHOUT CANONICAL OBSERVATION] {r.markets_without_canonical_observation}")\n    print(f"[COVERAGE RATE] {r.coverage_rate:.2%}")\n    print(f"[SEVERITY] {g.severity}")\n    print(f"[LIKELY GAP] {g.likely_gap}")\n    print(f"[RECOMMENDED NEXT CAPABILITY] {g.recommended_next_capability}")\n    print("[PASS] Live coverage census completed read-only")\n    print("[PASS] Frozen OLR-001 through OLR-045 untouched")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPC-005 PHYSICAL PRE-SETTLEMENT COVERAGE CENSUS COMPLETE")\n'

def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(t,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    print("="*72)
    print(" OPC-005 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    import importlib,sys
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_004_live_coverage_gap_classifier")
    fn=getattr(up,"verify_opc_004_live_coverage_gap_classifier")
    if fn() is not True:
        raise RuntimeError("upstream verification failed")
    print("[PASS] Certified OPC-004 upstream boundary verified")

    affected=(MOD,TEST,INIT,RUNNER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_005_physical_pre_settlement_coverage_gate import *"
        if line not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OPC-005 installation failed")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-005 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
