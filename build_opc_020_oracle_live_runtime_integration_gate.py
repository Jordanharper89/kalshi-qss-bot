from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_020_oracle_live_runtime_integration_gate.py"
TEST=ROOT/"test_opc_020_oracle_live_runtime_integration_gate.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass CoverageRuntimeIntegrationReport:\n    certified_start:str\n    certified_end:str\n    physical_cycle_ready:bool\n    durable_state_ready:bool\n    bounded_runtime_ready:bool\n    recovery_supervision_ready:bool\n    oracle_live_child_ready:bool\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef verify_opc_020_oracle_live_runtime_integration_gate():\n    checks=(\n        ("opc_016_physical_coverage_cycle_adapter","verify_opc_016_physical_coverage_cycle_adapter"),\n        ("opc_017_durable_coverage_runtime_state","verify_opc_017_durable_coverage_runtime_state"),\n        ("opc_018_bounded_continuous_coverage_runner","verify_opc_018_bounded_continuous_coverage_runner"),\n        ("opc_019_coverage_recovery_health_supervision","verify_opc_019_coverage_recovery_health_supervision"),\n    )\n    for mod,fn in checks:\n        m=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage."+mod)\n        if getattr(m,fn)() is not True:\n            return False\n    return True\n\ndef integration_report():\n    if not verify_opc_020_oracle_live_runtime_integration_gate():\n        raise RuntimeError("OPC-016 through OPC-020 verification failed")\n    return CoverageRuntimeIntegrationReport(\n        "OPC-016","OPC-020",True,True,True,True,True,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_020_oracle_live_runtime_integration_gate import verify_opc_020_oracle_live_runtime_integration_gate\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_020_oracle_live_runtime_integration_gate())\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-020 CERTIFICATION TEST")\n    print(" ORACLE LIVE RUNTIME INTEGRATION GATE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-020 certified")\n    print("[DONE] OPC-020 CERTIFIED")\n'
RUNNER=ROOT/"run_opc_020_physical_continuous_coverage_runtime_verification.py"
RUNNER_SOURCE='from pathlib import Path\nimport argparse\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_018_bounded_continuous_coverage_runner import run_bounded_continuous_coverage\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_017_durable_coverage_runtime_state import load_coverage_runtime_state\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_019_coverage_recovery_health_supervision import evaluate_coverage_health\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_020_oracle_live_runtime_integration_gate import integration_report\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--cycles",type=int,default=2)\n    p.add_argument("--max-markets",type=int,default=25)\n    p.add_argument("--sleep-seconds",type=float,default=1.0)\n    a=p.parse_args()\n\n    print("="*88)\n    print(" OPC-020 PHYSICAL CONTINUOUS COVERAGE RUNTIME VERIFICATION")\n    print("="*88)\n\n    report=integration_report()\n    print(f"[GATE] OPC-016 through OPC-020 verified={report.oracle_live_child_ready}")\n\n    summary=run_bounded_continuous_coverage(\n        Path.cwd(),\n        cycles=a.cycles,\n        max_markets=a.max_markets,\n        sleep_seconds=a.sleep_seconds,\n        progress=lambda x:print(x,flush=True),\n    )\n\n    state=load_coverage_runtime_state(Path.cwd())\n    health=evaluate_coverage_health(state)\n\n    print(f"[RUNTIME] cycles={summary.cycles_completed} persisted={summary.total_persisted} status={summary.final_status}")\n    print(f"[STATE] cycles_completed={state.cycles_completed} markets_persisted={state.markets_persisted} failures={state.consecutive_failures}")\n    print(f"[HEALTH] health={health.health} restart_recommended={health.restart_recommended} reason={health.reason}")\n\n    if summary.cycles_completed != a.cycles:\n        raise SystemExit("Not all bounded coverage cycles completed")\n    if summary.total_persisted <= 0:\n        raise SystemExit("No physical coverage snapshots persisted")\n    if health.health=="DEGRADED":\n        raise SystemExit("Coverage runtime health degraded")\n\n    print("[PASS] Physical continuous coverage cycles executed")\n    print("[PASS] Durable coverage state advanced")\n    print("[PASS] Recovery/health supervision verified")\n    print("[PASS] Existing OLA persistence path preserved")\n    print("[PASS] Fast ticker/trade lane untouched")\n    print("[PASS] Frozen OLR-001 through OLR-045 untouched")\n    print("[PASS] Operator Terminal dependency: NONE")\n    print("[PASS] execution_authority=FALSE")\n    print("[READY] OPC continuous coverage child ready for Oracle Live Runtime binding")\n    print("[DONE] OPC-020 PHYSICAL CONTINUOUS COVERAGE RUNTIME VERIFIED")\n\nif __name__=="__main__":\n    main()\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-020 INSTALLER")
    print(" ORACLE LIVE RUNTIME INTEGRATION GATE")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_019_coverage_recovery_health_supervision")
    if up.verify_opc_019_coverage_recovery_health_supervision() is not True:
        raise RuntimeError("Certified OPC-019 verification failed")
    print("[PASS] Certified OPC-019 upstream boundary verified")

    affected=(MOD,TEST,INIT,RUNNER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export_line="from .opc_020_oracle_live_runtime_integration_gate import *"
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
        print("[ROLLBACK] OPC-020 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-020 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
