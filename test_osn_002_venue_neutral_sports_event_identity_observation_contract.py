from qseries_v2.oracle_source_network.canonical.sports_event import SportsEventIdentity, SportsObservation
from qseries_v2.oracle_source_network.mapping.venue_reference import VenueEventReference

a = SportsEventIdentity("baseball","MLB","2026","Houston Astros","Seattle Mariners","2026-09-05T19:10:00Z")
b = SportsEventIdentity("baseball","MLB","2026","Houston Astros","Seattle Mariners","2026-09-05T19:10:00Z")
assert a.event_id == b.event_id
assert a.event_id.startswith("osn:sport:")
obs = SportsObservation(a,"mlb_statsapi","777","2026-09-05T18:00:00Z","scheduled")
assert obs.execution_authority is False
k = VenueEventReference("kalshi","KX-EXAMPLE",a.event_id)
p = VenueEventReference("polymarket","0xexample",a.event_id)
assert k.canonical_event_id == p.canonical_event_id
print("[PASS] OSN-002 venue-neutral sports identity contract certified")
