from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_004_live_coverage_gap_classifier.py"
TEST=ROOT/"test_opc_004_live_coverage_gap_classifier.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass CoverageGapClassification:\n    coverage_rate:float\n    severity:str\n    likely_gap:str\n    recommended_next_capability:str\n    execution_authority:bool=False\n\ndef classify_coverage_gap(result):\n    r=float(result.coverage_rate)\n    if result.sampled_markets==0:\n        return CoverageGapClassification(0,"UNKNOWN","NO_DENOMINATOR","verify_sampling",False)\n    if r>=.9:\n        return CoverageGapClassification(r,"LOW","MINOR_QUIET_MARKET_GAP","targeted_quiet_market_snapshot_coverage",False)\n    if r>=.6:\n        return CoverageGapClassification(r,"MODERATE","PARTIAL_PRE_SETTLEMENT_COVERAGE","expand_snapshot_and_canonical_admission_coverage",False)\n    if r>=.2:\n        return CoverageGapClassification(r,"HIGH","MAJOR_PRE_SETTLEMENT_COVERAGE_GAP","trace_acquisition_to_canonicalization_path",False)\n    return CoverageGapClassification(r,"CRITICAL","SYSTEMIC_PRE_SETTLEMENT_COVERAGE_GAP","build_universal_pre_settlement_snapshot_path",False)\n\ndef verify_opc_004_live_coverage_gap_classifier():\n    class X:\n        sampled_markets=100\n        coverage_rate=.1\n    return classify_coverage_gap(X()).severity=="CRITICAL"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_004_live_coverage_gap_classifier import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_004_live_coverage_gap_classifier())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-004 CERTIFICATION TEST")\n    print(" LIVE COVERAGE GAP CLASSIFIER")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Live pre-settlement coverage gap classification certified")\n    print("[DONE] OPC-004 CERTIFIED")\n'

def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(t,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    print("="*72)
    print(" OPC-004 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    import importlib,sys
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model")
    fn=getattr(up,"verify_opc_003_canonical_observation_coverage_read_model")
    if fn() is not True:
        raise RuntimeError("upstream verification failed")
    print("[PASS] Certified OPC-003 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_004_live_coverage_gap_classifier import *"
        if line not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OPC-004 installation failed")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-004 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
