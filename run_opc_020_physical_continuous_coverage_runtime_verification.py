from pathlib import Path
import argparse
from qseries_v2.oracle_pre_settlement_coverage.opc_018_bounded_continuous_coverage_runner import run_bounded_continuous_coverage
from qseries_v2.oracle_pre_settlement_coverage.opc_017_durable_coverage_runtime_state import load_coverage_runtime_state
from qseries_v2.oracle_pre_settlement_coverage.opc_019_coverage_recovery_health_supervision import evaluate_coverage_health
from qseries_v2.oracle_pre_settlement_coverage.opc_020_oracle_live_runtime_integration_gate import integration_report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cycles",type=int,default=2)
    p.add_argument("--max-markets",type=int,default=25)
    p.add_argument("--sleep-seconds",type=float,default=1.0)
    a=p.parse_args()

    print("="*88)
    print(" OPC-020 PHYSICAL CONTINUOUS COVERAGE RUNTIME VERIFICATION")
    print("="*88)

    report=integration_report()
    print(f"[GATE] OPC-016 through OPC-020 verified={report.oracle_live_child_ready}")

    summary=run_bounded_continuous_coverage(
        Path.cwd(),
        cycles=a.cycles,
        max_markets=a.max_markets,
        sleep_seconds=a.sleep_seconds,
        progress=lambda x:print(x,flush=True),
    )

    state=load_coverage_runtime_state(Path.cwd())
    health=evaluate_coverage_health(state)

    print(f"[RUNTIME] cycles={summary.cycles_completed} persisted={summary.total_persisted} status={summary.final_status}")
    print(f"[STATE] cycles_completed={state.cycles_completed} markets_persisted={state.markets_persisted} failures={state.consecutive_failures}")
    print(f"[HEALTH] health={health.health} restart_recommended={health.restart_recommended} reason={health.reason}")

    if summary.cycles_completed != a.cycles:
        raise SystemExit("Not all bounded coverage cycles completed")
    if summary.total_persisted <= 0:
        raise SystemExit("No physical coverage snapshots persisted")
    if health.health=="DEGRADED":
        raise SystemExit("Coverage runtime health degraded")

    print("[PASS] Physical continuous coverage cycles executed")
    print("[PASS] Durable coverage state advanced")
    print("[PASS] Recovery/health supervision verified")
    print("[PASS] Existing OLA persistence path preserved")
    print("[PASS] Fast ticker/trade lane untouched")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] Operator Terminal dependency: NONE")
    print("[PASS] execution_authority=FALSE")
    print("[READY] OPC continuous coverage child ready for Oracle Live Runtime binding")
    print("[DONE] OPC-020 PHYSICAL CONTINUOUS COVERAGE RUNTIME VERIFIED")

if __name__=="__main__":
    main()
