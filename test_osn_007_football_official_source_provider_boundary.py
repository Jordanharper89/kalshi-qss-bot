
import qseries_v2.oracle_source_network.providers.football_official
from qseries_v2.oracle_source_network.providers.league_registry import get
for league in ("NFL","NCAAF"):
    s = get(league)
    assert s.read_only is True
    assert s.execution_authority is False
    assert s.official_domain
print("[PASS] OSN-007 football provider boundary certified")
