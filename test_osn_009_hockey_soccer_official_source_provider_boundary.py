
import qseries_v2.oracle_source_network.providers.hockey_soccer_official
from qseries_v2.oracle_source_network.providers.league_registry import get
for league in ("NHL","MLS","EPL","UCL"):
    s = get(league)
    assert s.read_only is True
    assert s.execution_authority is False
    assert s.official_domain
print("[PASS] OSN-009 hockey + soccer provider boundary certified")
