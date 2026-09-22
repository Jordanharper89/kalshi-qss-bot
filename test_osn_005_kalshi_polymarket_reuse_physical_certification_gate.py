from qseries_v2.oracle_source_network.canonical.mlb import canonicalize_schedule
from qseries_v2.oracle_source_network.mapping.venue_reference import VenueEventReference
from qseries_v2.oracle_source_network.certification.reuse_gate import certify_reuse
from qseries_v2.oracle_source_network.certification.source_network_gate import certify_observation

sample = {"dates":[{"games":[{
  "gamePk":777777,
  "gameDate":"2026-09-05T19:10:00Z",
  "season":"2026",
  "status":{"abstractGameState":"Preview"},
  "teams":{
    "home":{"team":{"name":"Houston Astros"}},
    "away":{"team":{"name":"Seattle Mariners"}}
  }
}]}]}

obs = canonicalize_schedule(sample,"2026-09-05T18:00:00Z")[0]
gate = certify_observation(obs)
assert gate["passed"], gate

event_id = obs.identity.event_id
kalshi = VenueEventReference("kalshi","KX-MLB-HOU-SEA",event_id)
poly = VenueEventReference("polymarket","POLY-MLB-HOU-SEA",event_id)
reuse = certify_reuse(event_id,(kalshi,poly))

assert reuse.passed
assert reuse.canonical_observation_count == 1
assert reuse.alias_count == 2
assert reuse.duplicate_source_observations == 0
assert reuse.execution_authority is False
assert reuse.venues == ("kalshi","polymarket")

print("[PASS] source observation invariants certified")
print("[PASS] one canonical observation reused across Kalshi + Polymarket aliases")
print("[PASS] duplicate_source_observations=0")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-005 reuse certification boundary certified")
