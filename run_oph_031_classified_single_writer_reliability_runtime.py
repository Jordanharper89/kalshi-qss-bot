from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_031_classified_single_writer_reliability_runtime import run_classified_writer_forever
if __name__=="__main__":
    print("="*96,flush=True)
    print(" OPH-031 CLASSIFIED POSTGRESQL SINGLE-WRITER RELIABILITY RUNTIME",flush=True)
    print("="*96,flush=True)
    raise SystemExit(run_classified_writer_forever(Path.cwd(),lambda x:print(x,flush=True)))
