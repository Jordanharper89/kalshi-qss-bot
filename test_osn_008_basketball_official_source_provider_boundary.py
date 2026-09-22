
import qseries_v2.oracle_source_network.providers.basketball_official
from qseries_v2.oracle_source_network.providers.league_registry import get
for league in ("NBA","NCAAB"):
    s = get(league)
    assert s.read_only is True
    assert s.execution_authority is False
print("[PASS] OSN-008 basketball provider boundary certified")
