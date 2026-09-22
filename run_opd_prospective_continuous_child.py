from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import run_forever
if __name__=="__main__":
    run_forever(Path.cwd(),2.0)
