
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.physical_extraction_result import classify
from qseries_v2.oracle_source_network.certification.physical_extraction_admission import decide
from qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events
from qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events
from qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events
specs=(
("NFL","nfl_official","official_league","football"),
("NCAAF","ncaa_football_official","official_governing_body","football"),
("NBA","nba_official","official_league","basketball"),
("NCAAB","ncaa_basketball_official","official_governing_body","basketball"),
("NHL","nhl_official","official_league","hockey_soccer"),
("MLS","mls_official","official_league","hockey_soccer"),
("EPL","premier_league_official","official_league","hockey_soccer"))
admissions=[]
for league,provider,authority,family in specs:
    _,payload=acquire_live_payload(league,8.0)
    if family=="football":
        events=extract_football_events(payload["body"],league,provider,authority=authority)
    elif family=="basketball":
        events=extract_basketball_events(payload["body"],league,provider,authority=authority)
    else:
        events=extract_hockey_soccer_events(payload["body"],league,provider,authority=authority)
    r=classify(league,payload["body"],events)
    a=decide(r); admissions.append(a)
    print(f"[ADMISSION] {league} status={a.status} events={a.events} admitted={a.admitted}")
assert len(admissions)==7
assert all(a.execution_authority is False for a in admissions)
print("[CERT] physically_extracted_admitted=",tuple(a.league for a in admissions if a.admitted))
print("[CERT] held_for_structure_or_current_event_gap=",tuple(a.league for a in admissions if not a.admitted))
print("[PASS] OSN-038 reported physical extraction admission truth")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=75)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-038 exceeded hard 75-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-038 failed rc={p.returncode}"
print("[PASS] OSN-038 cross-league physical extraction admission gate certified")
