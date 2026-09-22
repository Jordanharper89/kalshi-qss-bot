from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_034_coverage_microbatch_yield_policy.py"
TEST=ROOT/"test_opc_034_coverage_microbatch_yield_policy.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_034_BUILD_ID="OPC-034"\nOPC_034_REVISION="OPC_034_COVERAGE_MICROBATCH_YIELD_POLICY_V1"\n\n@dataclass(frozen=True)\nclass CoverageYieldPolicy:\n    coverage_router_microbatch:int=25\n    full_page_chunk_target:int=200\n    fast_lane_preemption_enabled:bool=True\n    release_lock_between_microbatches:bool=True\n    execution_authority:bool=False\n\ndef coverage_yield_policy():\n    return CoverageYieldPolicy()\n\ndef estimate_fast_lane_blocking_units(page_missing,policy=None):\n    p=policy or coverage_yield_policy()\n    missing=max(0,int(page_missing))\n    if missing==0:\n        return 0\n    return (missing+p.coverage_router_microbatch-1)//p.coverage_router_microbatch\n\ndef verify_opc_034_coverage_microbatch_yield_policy():\n    p=coverage_yield_policy()\n    return (\n        p.coverage_router_microbatch==25\n        and p.fast_lane_preemption_enabled\n        and p.release_lock_between_microbatches\n        and estimate_fast_lane_blocking_units(1000,p)==40\n        and not p.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_034_coverage_microbatch_yield_policy import verify_opc_034_coverage_microbatch_yield_policy\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_034_coverage_microbatch_yield_policy())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-034 CERTIFICATION TEST")\n    print(" COVERAGE MICROBATCH YIELD POLICY")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-034 certified")\n    print("[DONE] OPC-034 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-034 INSTALLER")
    print(" COVERAGE MICROBATCH YIELD POLICY")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch")
    if up.verify_opc_033_priority_router_patch() is not True:
        raise RuntimeError("Certified OPC-033 verification failed")
    print("[PASS] Certified OPC-033 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_034_coverage_microbatch_yield_policy import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-034 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-034 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
