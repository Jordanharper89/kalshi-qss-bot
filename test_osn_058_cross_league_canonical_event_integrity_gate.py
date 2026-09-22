
from qseries_v2.oracle_source_network.certification.cross_league_canonical_integrity import validate
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

events=[
 CanonicalSportsEvent(league="NFL",season="2026",provider="test",home_team="A",away_team="B",scheduled_start="2026-09-01T00:00:00Z",source_observed_at="2026-09-01T00:00:01Z",source_authority="official_league",provider_event_id="1",event_discriminator="1"),
 CanonicalSportsEvent(league="MLS",season="2026",provider="test",home_team="C",away_team="D",scheduled_start="2026-09-01T01:00:00Z",source_observed_at="2026-09-01T00:00:01Z",source_authority="official_league",provider_event_id="2",event_discriminator="2"),
]
r=validate(events)
print("[INTEGRITY]",r)
assert r.passed and r.checked==2 and not r.failures
assert r.execution_authority is False
print("[PASS] OSN-058 cross-league canonical integrity gate certified")
