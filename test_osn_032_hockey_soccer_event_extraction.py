
import json
from qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events
payload={"matches":[
 {"matchId":"epl-1","homeTeam":{"name":"Arsenal"},"awayTeam":{"name":"Chelsea"},
  "startTime":"2026-09-12T14:00:00Z","status":"scheduled","matchweek":"4"},
 {"matchId":"nhl-1","homeTeam":{"name":"Dallas Stars"},"awayTeam":{"name":"Colorado Avalanche"},
  "startTime":"2026-10-05T00:00:00Z","status":"scheduled"}
]}
body='<script type="application/json">'+json.dumps(payload)+'</script>'
epl=extract_hockey_soccer_events(body,"EPL","premier_league_official")
assert len(epl)==2
assert epl[0].provider_event_id=="epl-1"
assert epl[0].event_discriminator=="4"
assert epl[0].execution_authority is False
print("[PASS] hockey/soccer official-page JSON event extraction certified")
print("[PASS] round/matchweek discriminator retained")
print("[PASS] OSN-032 hockey + soccer event extraction certified")
