from pathlib import Path
import runpy
from qseries_v2.oracle_production_hardening.oph_008_fast_lane_queue_migration import (
    install_fast_lane_queue_migration,
)

UNDERLYING_RUNNER='run_oad_054_kalshi_global_fast_lane.py'

if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-010 FAST LANE -> SHARED CANONICAL QUEUE",flush=True)
    print("="*88,flush=True)

    install_fast_lane_queue_migration(Path.cwd())

    print(
        f"[OPH] producer=FAST_LANE "
        f"direct_postgresql_write_authority=FALSE "
        f"underlying={UNDERLYING_RUNNER}",
        flush=True,
    )

    runpy.run_path(
        str(Path.cwd()/UNDERLYING_RUNNER),
        run_name="__main__",
    )
