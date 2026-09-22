
from pathlib import Path
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface import (
    render_persisted_trader_intelligence,
)

if __name__=="__main__":
    for line in render_persisted_trader_intelligence(Path.cwd(),10):
        print(line)
