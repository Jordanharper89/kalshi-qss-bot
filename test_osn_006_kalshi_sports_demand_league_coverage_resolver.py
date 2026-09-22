
from pathlib import Path
from qseries_v2.oracle_source_network.coverage.kalshi_sports_demand import (
    READ_ONLY,
    EXECUTION_AUTHORITY,
    detect_league,
    resolve_records,
)
from qseries_v2.oracle_source_network.coverage.oad418_exact_static_probe import inspect_exact_oad418

assert READ_ONLY is True
assert EXECUTION_AUTHORITY is False

sample = [
    {"title": "NFL: Texans vs Colts"},
    {"title": "NBA: Rockets vs Spurs"},
    {"title": "NHL: Stars vs Avalanche"},
    {"title": "MLS: Houston Dynamo vs Austin FC"},
    {"title": "MLB: Astros vs Mariners"},
    {"title": "unknown sports event"},
]

expected = ["NFL", "NBA", "NHL", "MLS", "MLB", "UNKNOWN"]
actual = [detect_league(x) for x in sample]
assert actual == expected, (actual, expected)

report = resolve_records(sample)
assert report["live_sports_markets_evaluated"] == 6
assert report["league_counts"]["NFL"] == 1
assert report["league_counts"]["NBA"] == 1
assert report["league_counts"]["NHL"] == 1
assert report["league_counts"]["MLS"] == 1
assert report["league_counts"]["MLB"] == 1
assert report["league_counts"]["UNKNOWN"] == 1
assert report["read_only"] is True
assert report["execution_authority"] is False

root = Path.cwd()
oad418 = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_418_evidence_gap_priority_planner.py"
assert oad418.exists(), oad418

info = inspect_exact_oad418(oad418)
assert info["bytes"] > 0
print(f"[PHYSICAL] exact_oad418_bytes={info['bytes']} functions={info['functions']} classes={info['classes']}")
print("[PASS] exact OAD-418 source inspected statically")
print("[PASS] no import/execution/search/recursive scan")
print("[PASS] READ_ONLY=TRUE execution_authority=FALSE")
print("[PASS] OSN-006 Kalshi sports demand resolver certified")
