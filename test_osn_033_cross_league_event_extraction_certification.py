
import json
from qseries_v2.oracle_source_network.certification.sports_event_extraction_gate import certify_events
from qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events
from qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events
from qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events

def wrap(obj):
    return '<script type="application/json">'+json.dumps(obj)+'</script>'

football=extract_football_events(wrap({"events":[
 {"id":"f1","homeTeam":{"name":"Team F1"},"awayTeam":{"name":"Team F2"},"startTime":"2026-09-10T18:00:00Z"},
 {"id":"f2","homeTeam":{"name":"Team F3"},"awayTeam":{"name":"Team F4"},"startTime":"2026-09-11T18:00:00Z"},
]}),"NFL","nfl_official")

basketball=extract_basketball_events(wrap({"games":[
 {"gameId":"b1","homeTeam":{"name":"Team B1"},"awayTeam":{"name":"Team B2"},"startDate":"2026-10-20T18:00:00Z"},
 {"gameId":"b2","homeTeam":{"name":"Team B3"},"awayTeam":{"name":"Team B4"},"startDate":"2026-10-21T18:00:00Z"},
]}),"NBA","nba_official")

hockey_soccer=extract_hockey_soccer_events(wrap({"matches":[
 {"matchId":"h1","homeTeam":{"name":"Team H1"},"awayTeam":{"name":"Team H2"},"startTime":"2026-10-05T18:00:00Z"},
 {"matchId":"s1","homeTeam":{"name":"Team S1"},"awayTeam":{"name":"Team S2"},"startTime":"2026-09-20T18:00:00Z","matchweek":"5"},
]}),"EPL","premier_league_official")

reports=[
 certify_events("football",football),
 certify_events("basketball",basketball),
 certify_events("hockey_soccer",hockey_soccer),
]
for r in reports:
    print(f"[CERT] category={r.category} events={r.events} unique_ids={r.unique_ids} stable_identity={r.stable_identity}")
assert all(r.events==2 for r in reports)
assert all(r.unique_ids==r.events for r in reports)
assert all(r.stable_identity for r in reports)
assert all(r.read_only for r in reports)
assert all(r.execution_authority is False for r in reports)
print("[PASS] cross-category canonical event extraction certified")
print("[PASS] no schedule-time identity drift introduced")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-033 cross-league event extraction certification complete")
