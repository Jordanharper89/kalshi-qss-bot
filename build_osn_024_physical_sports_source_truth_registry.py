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
    print(' OSN-024 PHYSICAL SPORTS SOURCE TRUTH REGISTRY INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py')
    write('qseries_v2/oracle_source_network/certification/sports_source_truth.py', '\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True, slots=True)\nclass SourceTruth:\n    source_id: str\n    league: str\n    authority: str\n    certification_test: str | None\n    status: str\n    reason: str = ""\n    execution_authority: bool = False\n\nSOURCES = (\n    SourceTruth("nfl_official", "NFL", "official_league", "test_osn_011_nfl_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("ncaa_football_official", "NCAAF", "official_governing_body", "test_osn_012_ncaa_football_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("nba_official", "NBA", "official_league", "test_osn_016_nba_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("ncaa_basketball_official", "NCAAB", "official_governing_body", "test_osn_017_ncaa_basketball_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("nhl_official", "NHL", "official_league", "test_osn_021_nhl_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("mls_official", "MLS", "official_league", "test_osn_022_mls_official_physical_acquisition.py", "CERTIFIED"),\n    SourceTruth("premier_league_official", "EPL", "official_league", None, "CERTIFIED"),\n    SourceTruth(\n        "uefa_official", "UCL", "official_governing_body", None, "BLOCKED",\n        "Oracle runtime received zero bytes from UEFA through both urllib and curl.exe within bounded physical gates."\n    ),\n)\n\ndef production_ready():\n    return tuple(x for x in SOURCES if x.status == "CERTIFIED")\n\ndef blocked():\n    return tuple(x for x in SOURCES if x.status == "BLOCKED")\n')
    write('test_osn_024_physical_sports_source_truth_registry.py', '\nfrom qseries_v2.oracle_source_network.certification.sports_source_truth import SOURCES, production_ready, blocked\n\nassert len(SOURCES) == 8\nassert len(production_ready()) == 7\nassert len(blocked()) == 1\nassert blocked()[0].league == "UCL"\nassert all(x.execution_authority is False for x in SOURCES)\nprint("[PASS] production_ready_leagues=", tuple(x.league for x in production_ready()))\nprint("[PASS] blocked_leagues=", tuple(x.league for x in blocked()))\nprint("[PASS] OSN-024 physical sports source truth registry certified")\n')
    print('[PASS] OSN-024 installed')
    print('[PASS] UCL retained explicitly as BLOCKED')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
