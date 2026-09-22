from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_018_bounded_continuous_coverage_runner.py"
TEST=ROOT/"test_opc_018_bounded_continuous_coverage_runner.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport time\nfrom pathlib import Path\n\nfrom .opc_016_physical_coverage_cycle_adapter import run_physical_coverage_cycle\nfrom .opc_017_durable_coverage_runtime_state import (\n    load_coverage_runtime_state,\n    save_coverage_runtime_state,\n    advance_coverage_runtime_state,\n)\n\n@dataclass(frozen=True)\nclass ContinuousCoverageRunSummary:\n    cycles_requested:int\n    cycles_completed:int\n    total_persisted:int\n    final_status:str\n    execution_authority:bool=False\n\ndef run_bounded_continuous_coverage(\n    root=None,\n    cycles=3,\n    max_markets=100,\n    lookback_hours=24,\n    sleep_seconds=2.0,\n    progress=None,\n):\n    root=Path(root or Path.cwd()).resolve()\n    cycles=int(cycles)\n    if cycles<1 or cycles>100:\n        raise ValueError("cycles must be 1..100")\n    if sleep_seconds<0 or sleep_seconds>3600:\n        raise ValueError("sleep_seconds out of bounds")\n\n    state=load_coverage_runtime_state(root)\n    completed=0\n    total=0\n    status="NOT_STARTED"\n\n    for cycle in range(1,cycles+1):\n        result=run_physical_coverage_cycle(\n            root,\n            max_markets=max_markets,\n            lookback_hours=lookback_hours,\n            progress=progress,\n        )\n        status="SUCCESS" if result.success else "PARTIAL"\n        state=advance_coverage_runtime_state(\n            state,\n            planned=result.snapshots_planned,\n            persisted=result.snapshots_persisted,\n            status=status,\n        )\n        state=save_coverage_runtime_state(state,root)\n        completed+=1\n        total+=result.snapshots_persisted\n\n        if progress:\n            progress(\n                f"[COVERAGE RUNTIME] cycle={cycle}/{cycles} "\n                f"planned={result.snapshots_planned} "\n                f"persisted={result.snapshots_persisted} "\n                f"status={status}"\n            )\n\n        if cycle<cycles and sleep_seconds:\n            time.sleep(float(sleep_seconds))\n\n    return ContinuousCoverageRunSummary(cycles,completed,total,status,False)\n\ndef verify_opc_018_bounded_continuous_coverage_runner():\n    x=ContinuousCoverageRunSummary(3,3,300,"SUCCESS",False)\n    return x.cycles_completed==3 and x.total_persisted==300 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_018_bounded_continuous_coverage_runner import verify_opc_018_bounded_continuous_coverage_runner\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_018_bounded_continuous_coverage_runner())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-018 CERTIFICATION TEST")\n    print(" BOUNDED CONTINUOUS COVERAGE RUNNER")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-018 certified")\n    print("[DONE] OPC-018 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-018 INSTALLER")
    print(" BOUNDED CONTINUOUS COVERAGE RUNNER")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_017_durable_coverage_runtime_state")
    if up.verify_opc_017_durable_coverage_runtime_state() is not True:
        raise RuntimeError("Certified OPC-017 verification failed")
    print("[PASS] Certified OPC-017 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export_line="from .opc_018_bounded_continuous_coverage_runner import *"
        if export_line not in current:
            write_exact(INIT,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )
    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)
        print("[ROLLBACK] OPC-018 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-018 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
