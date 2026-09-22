from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_029_adaptive_coverage_throughput_controller.py"
TEST=ROOT/"test_opc_029_adaptive_coverage_throughput_controller.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_029_BUILD_ID="OPC-029"\nOPC_029_REVISION="OPC_029_ADAPTIVE_COVERAGE_THROUGHPUT_CONTROLLER_V1"\n\n@dataclass(frozen=True)\nclass CoverageThroughputBudget:\n    chunk_size:int\n    inter_chunk_sleep_seconds:float\n    inter_page_sleep_seconds:float\n    max_retries:int\n    mode:str\n    execution_authority:bool=False\n\ndef choose_throughput_budget(*,recent_retries=0,recent_failures=0):\n    retries=int(recent_retries)\n    failures=int(recent_failures)\n\n    if failures>=2:\n        return CoverageThroughputBudget(50,0.50,2.0,7,"PROTECTIVE",False)\n    if retries>=3:\n        return CoverageThroughputBudget(75,0.25,1.0,6,"CAUTIOUS",False)\n    if retries>=1:\n        return CoverageThroughputBudget(100,0.10,0.25,5,"BALANCED",False)\n    return CoverageThroughputBudget(200,0.00,0.00,5,"MAX_THROUGHPUT",False)\n\ndef verify_opc_029_adaptive_coverage_throughput_controller():\n    fast=choose_throughput_budget()\n    cautious=choose_throughput_budget(recent_retries=4)\n    protective=choose_throughput_budget(recent_failures=2)\n    return (\n        fast.chunk_size==200 and fast.inter_page_sleep_seconds==0.0\n        and cautious.chunk_size<fast.chunk_size\n        and protective.chunk_size<=cautious.chunk_size\n        and not fast.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_029_adaptive_coverage_throughput_controller import verify_opc_029_adaptive_coverage_throughput_controller\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_029_adaptive_coverage_throughput_controller())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-029 CERTIFICATION TEST")\n    print(" ADAPTIVE COVERAGE THROUGHPUT CONTROLLER")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-029 certified")\n    print("[DONE] OPC-029 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-029 INSTALLER")
    print(" ADAPTIVE COVERAGE THROUGHPUT CONTROLLER")
    print("="*80)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_028_activity_tier_refresh_policy")
    if up.verify_opc_028_activity_tier_refresh_policy() is not True:
        raise RuntimeError("Certified OPC-028 verification failed")
    print("[PASS] Certified OPC-028 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_029_adaptive_coverage_throughput_controller import *"
        if export not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-029 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-029 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
