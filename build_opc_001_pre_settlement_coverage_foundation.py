from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_001_pre_settlement_coverage_foundation.py"
TEST=ROOT/"test_opc_001_pre_settlement_coverage_foundation.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass PreSettlementCoveragePolicy:\n    venue:str="KALSHI"\n    bounded_sampling:bool=True\n    read_only:bool=True\n    olr_access:str="READ_ONLY"\n    execution_authority:bool=False\n\ndef build_pre_settlement_coverage_policy():\n    return PreSettlementCoveragePolicy()\n\ndef verify_opc_001_pre_settlement_coverage_foundation():\n    p=build_pre_settlement_coverage_policy()\n    return p.venue=="KALSHI" and p.bounded_sampling and p.read_only and p.olr_access=="READ_ONLY" and not p.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_001_pre_settlement_coverage_foundation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_001_pre_settlement_coverage_foundation())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-001 CERTIFICATION TEST")\n    print(" PRE-SETTLEMENT COVERAGE FOUNDATION")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Live pre-settlement coverage policy certified")\n    print("[DONE] OPC-001 CERTIFIED")\n'

def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(t,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    print("="*72)
    print(" OPC-001 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    print('[PASS] OPC subsystem foundation install started')

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_001_pre_settlement_coverage_foundation import *"
        if line not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OPC-001 installation failed")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-001 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
