from pathlib import Path
from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_forever

if __name__=="__main__":
    run_forever(
        root=Path.cwd(),
        cadence_seconds=30.0,
        timeout=15,
    )
