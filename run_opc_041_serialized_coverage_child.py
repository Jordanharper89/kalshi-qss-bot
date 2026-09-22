from pathlib import Path
import runpy
from qseries_v2.oracle_pre_settlement_coverage.opc_040_coverage_serialized_persistence_integration import (
    install_coverage_serialized_persistence,
)

UNDERLYING_RUNNER='run_opc_030_high_throughput_coverage_child.py'

if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPC-041 SERIALIZED COVERAGE CANONICAL WRITER",flush=True)
    print("="*88,flush=True)

    install_coverage_serialized_persistence(Path.cwd())

    print(
        f"[SERIALIZED WRITER] writer=COVERAGE "
        f"microbatch=25 underlying={UNDERLYING_RUNNER}",
        flush=True,
    )

    runpy.run_path(
        str(Path.cwd()/UNDERLYING_RUNNER),
        run_name="__main__",
    )
