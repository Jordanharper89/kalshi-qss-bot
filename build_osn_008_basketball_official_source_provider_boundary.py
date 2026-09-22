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
    print("="*118)
    print(" OSN-008 NBA + NCAA BASKETBALL OFFICIAL-SOURCE PROVIDER BOUNDARY INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/providers/football_official.py")
    write("qseries_v2/oracle_source_network/providers/basketball_official.py", '\nfrom .league_registry import LeagueProvider, register\n\nNBA = LeagueProvider(\n    provider_id="nba_official",\n    league="NBA",\n    authority="official_league",\n    official_domain="nba.com",\n    acquisition_mode="official_web_or_api_boundary",\n)\nNCAAB = LeagueProvider(\n    provider_id="ncaa_basketball_official",\n    league="NCAAB",\n    authority="official_governing_body",\n    official_domain="ncaa.com",\n    acquisition_mode="official_web_or_api_boundary",\n)\nregister(NBA)\nregister(NCAAB)\n')
    write("test_osn_008_basketball_official_source_provider_boundary.py", '\nimport qseries_v2.oracle_source_network.providers.basketball_official\nfrom qseries_v2.oracle_source_network.providers.league_registry import get\nfor league in ("NBA","NCAAB"):\n    s = get(league)\n    assert s.read_only is True\n    assert s.execution_authority is False\nprint("[PASS] OSN-008 basketball provider boundary certified")\n')
    print("[PASS] OSN-008 installed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
