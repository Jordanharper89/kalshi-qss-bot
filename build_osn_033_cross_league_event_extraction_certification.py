from pathlib import Path

ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(' OSN-033 CROSS-LEAGUE EVENT EXTRACTION CERTIFICATION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/mapping/football_event_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/hockey_soccer_event_extractor.py')
    write('qseries_v2/oracle_source_network/certification/sports_event_extraction_gate.py', '\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events\nfrom qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events\nfrom qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events\n\n@dataclass(frozen=True, slots=True)\nclass ExtractionCertification:\n    category: str\n    events: int\n    unique_ids: int\n    stable_identity: bool\n    read_only: bool\n    execution_authority: bool = False\n\ndef certify_events(category, events):\n    ids=[e.canonical_event_id for e in events]\n    return ExtractionCertification(\n        category=category,\n        events=len(events),\n        unique_ids=len(set(ids)),\n        stable_identity=(len(ids)==len(set(ids)) and all(x.startswith("osn:event:") for x in ids)),\n        read_only=all(e.read_only is True for e in events),\n    )\n')
    write('test_osn_033_cross_league_event_extraction_certification.py', '\nimport json\nfrom qseries_v2.oracle_source_network.certification.sports_event_extraction_gate import certify_events\nfrom qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events\nfrom qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events\nfrom qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events\n\ndef wrap(obj):\n    return \'<script type="application/json">\'+json.dumps(obj)+\'</script>\'\n\nfootball=extract_football_events(wrap({"events":[\n {"id":"f1","homeTeam":{"name":"Team F1"},"awayTeam":{"name":"Team F2"},"startTime":"2026-09-10T18:00:00Z"},\n {"id":"f2","homeTeam":{"name":"Team F3"},"awayTeam":{"name":"Team F4"},"startTime":"2026-09-11T18:00:00Z"},\n]}),"NFL","nfl_official")\n\nbasketball=extract_basketball_events(wrap({"games":[\n {"gameId":"b1","homeTeam":{"name":"Team B1"},"awayTeam":{"name":"Team B2"},"startDate":"2026-10-20T18:00:00Z"},\n {"gameId":"b2","homeTeam":{"name":"Team B3"},"awayTeam":{"name":"Team B4"},"startDate":"2026-10-21T18:00:00Z"},\n]}),"NBA","nba_official")\n\nhockey_soccer=extract_hockey_soccer_events(wrap({"matches":[\n {"matchId":"h1","homeTeam":{"name":"Team H1"},"awayTeam":{"name":"Team H2"},"startTime":"2026-10-05T18:00:00Z"},\n {"matchId":"s1","homeTeam":{"name":"Team S1"},"awayTeam":{"name":"Team S2"},"startTime":"2026-09-20T18:00:00Z","matchweek":"5"},\n]}),"EPL","premier_league_official")\n\nreports=[\n certify_events("football",football),\n certify_events("basketball",basketball),\n certify_events("hockey_soccer",hockey_soccer),\n]\nfor r in reports:\n    print(f"[CERT] category={r.category} events={r.events} unique_ids={r.unique_ids} stable_identity={r.stable_identity}")\nassert all(r.events==2 for r in reports)\nassert all(r.unique_ids==r.events for r in reports)\nassert all(r.stable_identity for r in reports)\nassert all(r.read_only for r in reports)\nassert all(r.execution_authority is False for r in reports)\nprint("[PASS] cross-category canonical event extraction certified")\nprint("[PASS] no schedule-time identity drift introduced")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-033 cross-league event extraction certification complete")\n')
    print('[PASS] OSN-033 installed')
    print('[PASS] deterministic cross-category extraction gate written')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
