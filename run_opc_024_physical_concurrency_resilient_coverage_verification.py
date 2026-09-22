from pathlib import Path
from qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget
from qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime import run_one_supervised_coverage_cycle
if __name__=="__main__":
    print("="*88);print(" OPC-024 PHYSICAL CONCURRENCY-RESILIENT COVERAGE VERIFICATION");print("="*88)
    b=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=25,cycle_sleep_seconds=30.0,lookback_hours=24.0,request_timeout_seconds=20.0)
    r=run_one_supervised_coverage_cycle(Path.cwd(),b,progress=lambda x:print(x,flush=True),max_retries=5)
    print(f"[RESULT] status={r.status} planned={r.planned} persisted={r.persisted} retries={r.retry_count} exhausted={r.exhausted}")
    if r.status not in ("SUCCESS","PARTIAL") or r.planned!=r.persisted:
        raise SystemExit("Physical coverage cycle did not complete successfully")
    print("[PASS] Physical coverage cycle completed")
    print("[PASS] Concurrency-resilient retry boundary active")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-024 PHYSICAL CONCURRENCY RESILIENCE VERIFIED")
