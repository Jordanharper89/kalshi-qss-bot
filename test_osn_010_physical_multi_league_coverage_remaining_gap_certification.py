
from pathlib import Path

import qseries_v2.oracle_source_network.providers.football_official
import qseries_v2.oracle_source_network.providers.basketball_official
import qseries_v2.oracle_source_network.providers.hockey_soccer_official

from qseries_v2.oracle_source_network.providers.league_registry import all_specs
from qseries_v2.oracle_source_network.certification.multi_league_coverage_gate import build_coverage
from qseries_v2.oracle_source_network.certification.oad418_exact_literal_coverage_probe import extract_literal_records

# MLB was physically certified in OSN-004; the other leagues are registered source boundaries.
covered = {"MLB"} | {spec.league for spec in all_specs()}

# Deterministic accounting proof.
sample = [
    {"title":"MLB Astros vs Mariners"},
    {"title":"NFL Texans vs Colts"},
    {"title":"NCAAF Texas vs Oklahoma"},
    {"title":"NBA Rockets vs Spurs"},
    {"title":"NCAAB Duke vs UNC"},
    {"title":"NHL Stars vs Avalanche"},
    {"title":"MLS Dynamo vs Austin"},
    {"title":"EPL Arsenal vs Chelsea"},
    {"title":"UCL Real Madrid vs Inter"},
    {"title":"unknown sports market"},
]

demo = build_coverage(sample, covered)
assert demo["live_sports_markets_evaluated"] == 10
assert demo["markets_with_official_source_candidate"] == 9
assert demo["markets_without_official_source_candidate"] == 1
assert demo["coverage_percentage"] == 90.0
assert demo["execution_authority"] is False
assert demo["remaining_unresolved_leagues"].get("UNKNOWN") == 1

root = Path.cwd()
oad418 = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_418_evidence_gap_priority_planner.py"
assert oad418.exists(), oad418

records = extract_literal_records(oad418)
print(f"[PHYSICAL] exact_oad418_literal_records={len(records)}")

if records:
    report = build_coverage(records, covered)
    for key, value in report.items():
        print(f"[COVERAGE] {key}={value}")
else:
    print("[INFO] exact OAD-418 source exposes no row-level literal market records")
    print("[INFO] physical market coverage percentage withheld rather than fabricated")

print("[PASS] OSN-010 deterministic multi-league coverage accounting certified")
print("[PASS] exact OAD-418 inspected statically only")
print("[PASS] no dynamic import / no OAD-418 execution / no recursive filesystem scan")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-010 remaining-gap certification boundary certified")
