
import json
from qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events
payload={"games":[
 {"gameId":"nba-1","homeTeam":{"name":"Houston Rockets"},"awayTeam":{"name":"Dallas Mavericks"},
  "startDate":"2026-10-20T00:00:00Z","status":"scheduled"},
 {"gameId":"nba-2","homeTeam":{"name":"Los Angeles Lakers"},"awayTeam":{"name":"Phoenix Suns"},
  "startDate":"2026-10-21T00:00:00Z","status":"scheduled"}
]}
body='<script type="application/json">'+json.dumps(payload)+'</script>'
events=extract_basketball_events(body,"NBA","nba_official")
assert len(events)==2
assert events[0].provider_event_id=="nba-1"
assert events[0].home_team=="Houston Rockets"
assert events[0].execution_authority is False
print("[PASS] basketball official-page JSON event extraction certified")
print("[PASS] provider event IDs preserved")
print("[PASS] OSN-031 basketball event extraction certified")
