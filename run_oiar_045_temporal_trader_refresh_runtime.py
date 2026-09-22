
from pathlib import Path
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_045_temporal_trader_refresh_runtime import run_temporal_trader_refresh
if __name__=="__main__":
    print(run_temporal_trader_refresh(Path.cwd()))
