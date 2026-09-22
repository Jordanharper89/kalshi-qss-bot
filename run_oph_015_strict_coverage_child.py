from pathlib import Path
import runpy
from qseries_v2.oracle_production_hardening.oph_013_strict_coverage_queue_only_admission import (
    install_strict_coverage_queue_only,
)
UNDERLYING_RUNNER='run_opc_030_high_throughput_coverage_child.py'
if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-015 STRICT COVERAGE -> QUEUE ONLY",flush=True)
    print("="*88,flush=True)
    install_strict_coverage_queue_only(Path.cwd())
    print("[OPH] producer=COVERAGE direct_postgresql_write_authority=FALSE mode=STRICT_QUEUE_ONLY",flush=True)
    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")
