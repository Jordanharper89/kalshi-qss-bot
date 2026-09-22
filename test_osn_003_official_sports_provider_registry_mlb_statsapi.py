import qseries_v2.oracle_source_network.providers.mlb_statsapi as mlb
from qseries_v2.oracle_source_network.providers.registry import get

spec = get("mlb_statsapi")
assert spec.authority == "official_league"
assert spec.read_only is True
assert spec.execution_authority is False
assert spec.base_url.startswith("https://statsapi.mlb.com/")
u = mlb.schedule_url("2026-09-05")
assert "sportId=1" in u and "date=2026-09-05" in u
print("[PASS] OSN-003 official provider registry + MLB provider certified")
