from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import run_exclusive_writer_forever
if __name__=="__main__":
    print("="*96,flush=True);print(" OPH-021 EXCLUSIVE POSTGRESQL UNIVERSAL CANONICAL WRITER",flush=True);print("="*96,flush=True)
    raise SystemExit(run_exclusive_writer_forever(Path.cwd(),lambda x:print(x,flush=True)))
