
from qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

e=CanonicalSportsEvent(
 league="NFL",season="2026",provider="fixture",
 home_team="A",away_team="B",
 scheduled_start="2026-09-06T00:00:00Z",
 source_observed_at="2026-09-05T23:59:00Z",
 source_authority="official_league",
 provider_event_id="evt-1",event_discriminator="evt-1",
)
x=from_canonical_event(e)
print("[SPORTS_PERSISTENCE]",x)
assert set(x.__dict__)=={"source_id","observed_at","observation_type","provider","subject","provenance_hash","payload","source_class"}
assert x.payload["canonical_event_id"]==e.canonical_event_id
assert x.payload["read_only"] is True
assert x.payload["execution_authority"] is False
print("[PASS] OSN-061 exact OAD-261 eight-field sports persistence contract certified")
