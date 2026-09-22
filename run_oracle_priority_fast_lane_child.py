from pathlib import Path
import runpy
from qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import install_priority_router_patch

UNDERLYING_RUNNER='run_oad_054_kalshi_global_fast_lane.py'

if __name__=="__main__":
    print("="*80,flush=True)
    print(" ORACLE FAST-LANE PRIORITY PERSISTENCE WRAPPER",flush=True)
    print("="*80,flush=True)
    install_priority_router_patch("fast_lane",Path.cwd())
    print(f"[PRIORITY] FAST_LANE writer arbitration active underlying={UNDERLYING_RUNNER}",flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")
