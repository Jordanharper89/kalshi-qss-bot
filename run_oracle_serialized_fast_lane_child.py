from pathlib import Path
import runpy
from qseries_v2.oracle_pre_settlement_coverage.opc_039_fast_lane_serialized_admission import (
    install_fast_lane_serialized_admission,
)

UNDERLYING_RUNNER='run_oad_054_kalshi_global_fast_lane.py'

if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPC-041 SERIALIZED FAST-LANE CANONICAL WRITER",flush=True)
    print("="*88,flush=True)

    install_fast_lane_serialized_admission(Path.cwd())

    print(
        f"[SERIALIZED WRITER] writer=FAST_LANE "
        f"underlying={UNDERLYING_RUNNER}",
        flush=True,
    )

    runpy.run_path(
        str(Path.cwd()/UNDERLYING_RUNNER),
        run_name="__main__",
    )
