from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    run_single_writer_forever,
)

if __name__=="__main__":
    print("="*88,flush=True)
    print(" OPH-010 ORACLE SINGLE CANONICAL POSTGRESQL WRITER",flush=True)
    print("="*88,flush=True)
    raise SystemExit(
        run_single_writer_forever(
            Path.cwd(),
            lambda x:print(x,flush=True),
        )
    )
