
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent, reconcile_schedule

a = CanonicalSportsEvent(
    league="NFL", season="2026", provider="nfl_official",
    provider_event_id="GAME-123", home_team="Houston Texans", away_team="Dallas Cowboys",
    scheduled_start="2026-09-10T19:00:00Z", source_observed_at="2026-09-05T20:00:00Z",
    source_authority="official_league",
)
b = CanonicalSportsEvent(
    league="NFL", season="2026", provider="nfl_official",
    provider_event_id="GAME-123", home_team="Houston Texans", away_team="Dallas Cowboys",
    scheduled_start="2026-09-11T19:00:00Z", source_observed_at="2026-09-06T20:00:00Z",
    source_authority="official_league",
)
assert a.canonical_event_id == b.canonical_event_id
r = reconcile_schedule(a, b)
assert r.canonical_event_id == a.canonical_event_id
assert r.schedule_revision == 1

f1 = CanonicalSportsEvent(
    league="EPL", season="2026-27", provider="premier_league_official",
    home_team="Club A", away_team="Club B", event_discriminator="matchweek-7",
    scheduled_start="2026-10-01T14:00:00Z", source_observed_at="2026-09-05T20:00:00Z",
    source_authority="official_league",
)
f2 = f1.rescheduled("2026-10-02T14:00:00Z")
assert f1.canonical_event_id == f2.canonical_event_id
assert f2.schedule_revision == 1
assert a.execution_authority is False and f1.execution_authority is False
print("[PASS] provider event identity survives reschedule")
print("[PASS] fallback identity excludes scheduled_start")
print("[PASS] schedule_revision advances without identity drift")
print("[PASS] OSN-029 stable canonical sports event identity V2 certified")
