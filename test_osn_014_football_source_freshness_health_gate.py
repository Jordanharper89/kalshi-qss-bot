
from qseries_v2.oracle_source_network.health.football_source_health import evaluate

x = {
    "provider":"nfl_official",
    "observed_at":"2026-09-05T12:00:00Z",
    "payload_sha256":"b"*64,
}
h = evaluate(x, now_iso="2026-09-05T12:01:00Z", max_age_seconds=120)
assert h.fresh is True
assert h.age_seconds == 60
assert h.payload_present is True
assert h.execution_authority is False

h2 = evaluate(x, now_iso="2026-09-05T12:05:00Z", max_age_seconds=120)
assert h2.fresh is False
print("[PASS] OSN-014 football source freshness/health gate certified")
