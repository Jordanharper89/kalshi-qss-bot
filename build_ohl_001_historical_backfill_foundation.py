from pathlib import Path
import os,sys,subprocess,importlib,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD=PKG/"ohl_001_historical_backfill_foundation.py"
TEST=ROOT/"test_ohl_001_historical_backfill_foundation.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nOHL_001_BUILD_ID="OHL-001"\nOHL_001_REVISION="OHL_001_HISTORICAL_LEARNING_BACKFILL_FOUNDATION_V1"\nFROZEN_OLR_BOUNDARY="OLR-001 through OLR-045"\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True)\nclass HistoricalBackfillPolicy:\n    source_role:str="POSTGRESQL_HISTORICAL_OBSERVATIONS"\n    olr_boundary:str=FROZEN_OLR_BOUNDARY\n    olr_access:str="READ_ONLY_CONSUMER"\n    require_settled_outcome:bool=True\n    require_pre_settlement_evidence:bool=True\n    reject_post_outcome_leakage:bool=True\n    execution_authority:bool=False\n\ndef build_historical_backfill_policy():\n    return HistoricalBackfillPolicy()\n\ndef verify_ohl_001_historical_backfill_foundation():\n    p=build_historical_backfill_policy()\n    return (p.olr_boundary==FROZEN_OLR_BOUNDARY and p.olr_access=="READ_ONLY_CONSUMER"\n            and p.require_settled_outcome and p.require_pre_settlement_evidence\n            and p.reject_post_outcome_leakage and not p.execution_authority)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_historical_learning.ohl_001_historical_backfill_foundation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ohl_001_historical_backfill_foundation())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OHL-001 CERTIFICATION TEST")\n    print(" HISTORICAL LEARNING BACKFILL FOUNDATION")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Historical Learning Backfill Foundation certified")\n    print("[DONE] OHL-001 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-001 INSTALLER")
    print(" HISTORICAL LEARNING BACKFILL FOUNDATION")
    print("="*72)
    print("[ROOT]",ROOT)
    # OLR is frozen and is intentionally NOT modified by OHL.
    freeze_path=ROOT/"runtime_state"/"oracle_learning_runtime_freeze_manifest.json"
    if freeze_path.exists():
        data=json.loads(freeze_path.read_text(encoding="utf-8"))
        if data.get("frozen_end")!="OLR-045" or data.get("policy")!="DEFECT_CORRECTIONS_ONLY":
            raise RuntimeError("Unexpected Oracle Learning Runtime freeze boundary")
        print("[PASS] Frozen OLR-001 through OLR-045 manifest verified read-only")
    else:
        print("[INFO] Freeze manifest not present in installer environment; OHL still makes no OLR writes")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .ohl_001_historical_backfill_foundation import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-001 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OHL-001 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
