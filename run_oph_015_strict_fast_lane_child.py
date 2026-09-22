from pathlib import Path
import runpy
from qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission import (
    install_strict_fast_lane_queue_only,
)
UNDERLYING_RUNNER='run_oad_054_kalshi_global_fast_lane.py'
if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-015 STRICT FAST LANE -> QUEUE ONLY",flush=True)
    print("="*88,flush=True)
    install_strict_fast_lane_queue_only(Path.cwd())
    print("[OPH] producer=FAST_LANE direct_postgresql_write_authority=FALSE mode=STRICT_QUEUE_ONLY",flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")
