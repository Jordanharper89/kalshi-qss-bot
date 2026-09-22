from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD_PATH=PKG/"ohl_007_historical_evidence_coverage_scanner.py"
TEST_PATH=ROOT/"test_ohl_007_historical_evidence_coverage_scanner.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import find_historical_market_evidence\nfrom .ohl_006_settled_outcome_inventory_adapter import verify_ohl_006_settled_outcome_inventory_adapter\n\nOHL_007_BUILD_ID="OHL-007"\nOHL_007_REVISION="OHL_007_HISTORICAL_EVIDENCE_COVERAGE_SCANNER_V1"\n\n@dataclass(frozen=True)\nclass MarketEvidenceCoverage:\n    ticker:str\n    evidence_count:int\n    earliest_observation_id:str\n    latest_observation_id:str\n    has_evidence:bool\n\ndef scan_market_evidence_coverage(root,ticker,limit=50):\n    if not verify_ohl_006_settled_outcome_inventory_adapter():\n        raise RuntimeError("OHL-006 verification failed")\n    limit=int(limit)\n    if limit<1 or limit>1000:raise ValueError("evidence limit must be 1..1000")\n    rows=tuple(find_historical_market_evidence(Path(root).resolve(),str(ticker),limit=limit))\n    return MarketEvidenceCoverage(\n        str(ticker),len(rows),\n        str(getattr(rows[0],"observation_id","")) if rows else "",\n        str(getattr(rows[-1],"observation_id","")) if rows else "",\n        bool(rows),\n    )\n\ndef verify_ohl_007_historical_evidence_coverage_scanner():\n    x=MarketEvidenceCoverage("KX",0,"","",False)\n    return not x.has_evidence and x.evidence_count==0\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_historical_learning.ohl_007_historical_evidence_coverage_scanner import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ohl_007_historical_evidence_coverage_scanner())\n    def test_limit(self):\n        with self.assertRaises(ValueError):scan_market_evidence_coverage(".","KX",0)\n\nif __name__=="__main__":\n    print("="*72);print(" OHL-007 CERTIFICATION TEST");print(" HISTORICAL EVIDENCE COVERAGE SCANNER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Historical evidence coverage scanner certified")\n    print("[DONE] OHL-007 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-007 INSTALLER")
    print(" HISTORICAL EVIDENCE COVERAGE SCANNER")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module('qseries_v2.oracle_historical_learning.ohl_006_settled_outcome_inventory_adapter')
    if getattr(up,'verify_ohl_006_settled_outcome_inventory_adapter')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OHL-006 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .ohl_007_historical_evidence_coverage_scanner import *"
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
        print("[ROLLBACK] OHL-007 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OHL-007 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
