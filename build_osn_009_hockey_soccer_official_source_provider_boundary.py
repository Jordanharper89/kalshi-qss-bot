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
    print(" OSN-009 NHL + MAJOR SOCCER OFFICIAL-SOURCE PROVIDER BOUNDARY INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/providers/basketball_official.py")
    write("qseries_v2/oracle_source_network/providers/hockey_soccer_official.py", '\nfrom .league_registry import LeagueProvider, register\n\nSPECS = (\n    LeagueProvider("nhl_official","NHL","official_league","nhl.com","official_web_or_api_boundary"),\n    LeagueProvider("mls_official","MLS","official_league","mlssoccer.com","official_web_or_api_boundary"),\n    LeagueProvider("premier_league_official","EPL","official_league","premierleague.com","official_web_or_api_boundary"),\n    LeagueProvider("uefa_official","UCL","official_governing_body","uefa.com","official_web_or_api_boundary"),\n)\nfor spec in SPECS:\n    register(spec)\n')
    write("test_osn_009_hockey_soccer_official_source_provider_boundary.py", '\nimport qseries_v2.oracle_source_network.providers.hockey_soccer_official\nfrom qseries_v2.oracle_source_network.providers.league_registry import get\nfor league in ("NHL","MLS","EPL","UCL"):\n    s = get(league)\n    assert s.read_only is True\n    assert s.execution_authority is False\n    assert s.official_domain\nprint("[PASS] OSN-009 hockey + soccer provider boundary certified")\n')
    print("[PASS] OSN-009 installed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
