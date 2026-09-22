
import json
from qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events

payload = {
  "events":[
    {"id":"nfl-1","homeTeam":{"name":"Houston Texans"},"awayTeam":{"name":"Dallas Cowboys"},
     "startTime":"2026-09-10T19:00:00Z","status":"scheduled","week":"1"},
    {"id":"nfl-2","homeTeam":{"name":"Kansas City Chiefs"},"awayTeam":{"name":"Denver Broncos"},
     "startTime":"2026-09-11T19:00:00Z","status":"scheduled","week":"1"}
  ]
}
body='<script type="application/json">'+json.dumps(payload)+'</script>'
events=extract_football_events(body,"NFL","nfl_official")
assert len(events)==2
assert events[0].provider_event_id=="nfl-1"
assert events[0].home_team=="Houston Texans"
assert events[0].execution_authority is False
assert events[0].canonical_event_id.startswith("osn:event:")
print("[PASS] football official-page JSON event extraction certified")
print("[PASS] provider event IDs preserved")
print("[PASS] OSN-030 football event extraction certified")
