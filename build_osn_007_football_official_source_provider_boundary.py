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
    print(" OSN-007 NFL + NCAA FOOTBALL OFFICIAL-SOURCE PROVIDER BOUNDARY INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py")
    write("qseries_v2/oracle_source_network/providers/league_registry.py", '\n"""Multi-league official-source provider catalog."""\nfrom dataclasses import dataclass\nfrom typing import Dict, Tuple\n\n@dataclass(frozen=True)\nclass LeagueProvider:\n    provider_id: str\n    league: str\n    authority: str\n    official_domain: str\n    acquisition_mode: str\n    read_only: bool = True\n    execution_authority: bool = False\n\n_REGISTRY: Dict[str, LeagueProvider] = {}\n\ndef register(spec: LeagueProvider):\n    if not spec.read_only or spec.execution_authority:\n        raise ValueError("OSN providers must remain read-only")\n    key = spec.league.upper()\n    if key in _REGISTRY and _REGISTRY[key] != spec:\n        raise ValueError(f"league provider collision: {key}")\n    _REGISTRY[key] = spec\n\ndef get(league: str):\n    return _REGISTRY[league.upper()]\n\ndef has(league: str) -> bool:\n    return league.upper() in _REGISTRY\n\ndef all_specs() -> Tuple[LeagueProvider, ...]:\n    return tuple(_REGISTRY[k] for k in sorted(_REGISTRY))\n')
    write("qseries_v2/oracle_source_network/providers/football_official.py", '\nfrom .league_registry import LeagueProvider, register\n\nNFL = LeagueProvider(\n    provider_id="nfl_official",\n    league="NFL",\n    authority="official_league",\n    official_domain="nfl.com",\n    acquisition_mode="official_web_or_api_boundary",\n)\nNCAAF = LeagueProvider(\n    provider_id="ncaa_football_official",\n    league="NCAAF",\n    authority="official_governing_body",\n    official_domain="ncaa.com",\n    acquisition_mode="official_web_or_api_boundary",\n)\nregister(NFL)\nregister(NCAAF)\n')
    write("test_osn_007_football_official_source_provider_boundary.py", '\nimport qseries_v2.oracle_source_network.providers.football_official\nfrom qseries_v2.oracle_source_network.providers.league_registry import get\nfor league in ("NFL","NCAAF"):\n    s = get(league)\n    assert s.read_only is True\n    assert s.execution_authority is False\n    assert s.official_domain\nprint("[PASS] OSN-007 football provider boundary certified")\n')
    print("[PASS] OSN-007 installed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
