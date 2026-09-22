from pathlib import Path
from qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget
from qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime import run_supervised_coverage_forever
if __name__=="__main__":
    print("="*72,flush=True);print(" OPC-025 CONTINUOUS UNIVERSAL PRE-SETTLEMENT COVERAGE CHILD",flush=True);print("="*72,flush=True)
    b=CoverageLoadBudget();print(f"[COVERAGE] page_limit={b.page_limit} max_snapshots_per_cycle={b.max_snapshots_per_cycle} sleep_seconds={b.cycle_sleep_seconds}",flush=True)
    raise SystemExit(run_supervised_coverage_forever(Path.cwd(),b,lambda x:print(x,flush=True)))
