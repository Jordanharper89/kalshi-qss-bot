
import subprocess,sys
from qseries_v2.oracle_source_network.mapping.ncaaf_exact_scoreboard_extractor import extract_ncaaf_live_events

sample=r"""
<html><script type="application/json">
{
  "scoreboard":{
    "seasonYear":"2026",
    "initialGames":[
      {
        "__typename":"Contest",
        "contestId":6604316,
        "gameState":"F",
        "statusCodeDisplay":"final",
        "startTimeEpoch":1788019200,
        "startTime":"12:00",
        "startDate":"08/29/2026",
        "teams":[
          {"__typename":"ContestTeam","isHome":true,"nameShort":"TCU","score":10},
          {"__typename":"ContestTeam","isHome":false,"nameShort":"UNC","score":7}
        ]
      }
    ]
  }
}
</script></html>
"""

events=extract_ncaaf_live_events(sample,observed_at="2026-09-05T00:00:00Z")
assert len(events)==1
e=events[0]
assert e.home_team=="TCU"
assert e.away_team=="UNC"
assert e.provider_event_id=="6604316"
assert e.home_score==10
assert e.away_score==7
print("[PASS] exact NCAA scoreboard schema regression certified")

probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.mapping.ncaaf_exact_scoreboard_extractor import extract_ncaaf_live_events

_,payload=acquire_live_payload("NCAAF",8.0)
events=extract_ncaaf_live_events(payload["body"])

print(f"[PHYSICAL] NCAAF bytes={len(payload['body'].encode('utf-8'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:12]:
    print(
        f"[EVENT] {e.away_team} @ {e.home_team} "
        f"start={e.scheduled_start} status={e.status} "
        f"score={e.away_score}-{e.home_score} provider_event_id={e.provider_event_id}"
    )

assert len(events)>0, "physically proven scoreboard.initialGames schema produced zero NCAAF events"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.provider_event_id for e in events)
assert all(e.home_team and e.away_team and e.scheduled_start for e in events)
assert all(e.read_only and e.execution_authority is False for e in events)

print("[PASS] NCAAF exact scoreboard.initialGames extraction physically certified")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-045 exact extractor repair exceeded hard 30-second gate")

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode==0, f"OSN-045 exact extractor repair failed rc={p.returncode}"
print("[PASS] OSN-045 repaired NCAAF exact live event extractor certified")
