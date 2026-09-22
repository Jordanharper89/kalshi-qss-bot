
import subprocess
import sys

from qseries_v2.oracle_source_network.canonical.mlb import canonicalize_schedule

sample = {
    "dates": [{
        "games": [{
            "gamePk": 12345,
            "gameDate": "2026-09-05T19:10:00Z",
            "season": "2026",
            "status": {"abstractGameState": "Live"},
            "teams": {
                "home": {"team": {"name": "Houston Astros"}, "score": 3},
                "away": {"team": {"name": "Seattle Mariners"}, "score": 2},
            },
        }]
    }]
}

rows = canonicalize_schedule(sample, "2026-09-05T20:00:00Z")
assert len(rows) == 1
x = rows[0]
assert x.provider == "mlb_statsapi"
assert x.identity.league == "MLB"
assert x.identity.event_id.startswith("osn:sport:")
assert x.home_score == 3
assert x.away_score == 2
assert x.execution_authority is False
assert x.source_authority == "official_league"
assert len(x.payload_sha256) == 64
print("[PASS] deterministic MLB canonicalization certified")

probe = """
from datetime import date
from qseries_v2.oracle_source_network.acquisition.mlb_live import acquire_date

rows = acquire_date(str(date.today()), timeout=8.0)
print(f"[PHYSICAL] official_mlb_events={len(rows)}")

assert isinstance(rows, tuple)
for row in rows:
    assert row.provider == "mlb_statsapi"
    assert row.source_authority == "official_league"
    assert row.execution_authority is False
    assert row.provider_event_id
    assert row.identity.event_id.startswith("osn:sport:")
    assert len(row.payload_sha256) == 64

print("[PASS] official MLB physical read completed")
"""

try:
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        text=True,
        capture_output=True,
        timeout=15,
    )
except subprocess.TimeoutExpired:
    raise AssertionError("official MLB physical probe exceeded hard 15-second wall-clock gate")

if completed.stdout:
    print(completed.stdout.rstrip())
if completed.stderr:
    print(completed.stderr.rstrip())

assert completed.returncode == 0, (
    "official MLB physical probe failed with return code " + str(completed.returncode)
)

print("[PASS] physical probe wall-clock bounded <=15 seconds")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-004 MLB official live acquisition certified")
