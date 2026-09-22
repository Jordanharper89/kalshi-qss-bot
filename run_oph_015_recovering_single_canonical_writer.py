from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_014_canonical_writer_failure_recovery_runtime import (
    run_recovering_single_writer_forever,
)
if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-015 RECOVERING SINGLE CANONICAL POSTGRESQL WRITER",flush=True)
    print("="*88,flush=True)
    raise SystemExit(
        run_recovering_single_writer_forever(
            Path.cwd(),
            lambda x:print(x,flush=True),
        )
    )
