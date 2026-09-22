from pathlib import Path
import runpy
from qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import install_priority_router_patch

UNDERLYING_RUNNER='run_opc_030_high_throughput_coverage_child.py'

if __name__=="__main__":
    print("="*80,flush=True)
    print(" ORACLE COVERAGE YIELDING PERSISTENCE WRAPPER",flush=True)
    print("="*80,flush=True)
    install_priority_router_patch("coverage",Path.cwd())
    print(f"[PRIORITY] COVERAGE writer arbitration active microbatch=25 underlying={UNDERLYING_RUNNER}",flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")
