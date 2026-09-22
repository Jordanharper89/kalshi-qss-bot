from pathlib import Path
import runpy
from qseries_v2.oracle_production_hardening.oph_009_coverage_queue_migration import (
    install_coverage_queue_migration,
)

UNDERLYING_RUNNER='run_opc_030_high_throughput_coverage_child.py'

if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-010 COVERAGE -> SHARED CANONICAL QUEUE",flush=True)
    print("="*88,flush=True)

    install_coverage_queue_migration(Path.cwd())

    print(
        f"[OPH] producer=COVERAGE "
        f"direct_postgresql_write_authority=FALSE "
        f"underlying={UNDERLYING_RUNNER}",
        flush=True,
    )

    runpy.run_path(
        str(Path.cwd()/UNDERLYING_RUNNER),
        run_name="__main__",
    )
