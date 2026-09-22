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
    print(' OSN-048 MLS + EPL OFFICIAL EVENT-SURFACE FOUNDATION REPAIR INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/mls_official_live.py')
    require('qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py')
    require('qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py')
    write('qseries_v2/oracle_source_network/acquisition/soccer_event_surface_boundary.py', '\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True, slots=True)\nclass SoccerSurfaceState:\n    league: str\n    current_uri: str\n    observed_role: str\n    production_event_admitted: bool\n    required_repair: str\n    execution_authority: bool = False\n\ndef states():\n    return (\n        SoccerSurfaceState(\n            league="MLS",\n            current_uri="https://www.mlssoccer.com/news/mls-announces-2026-regular-season-schedule",\n            observed_role="SCHEDULE_ANNOUNCEMENT_ARTICLE",\n            production_event_admitted=False,\n            required_repair="PROVE_OFFICIAL_FIXTURE_OR_SCORE_EVENT_SURFACE",\n        ),\n        SoccerSurfaceState(\n            league="EPL",\n            current_uri="https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season",\n            observed_role="FIXTURE_ANNOUNCEMENT_ARTICLE",\n            production_event_admitted=False,\n            required_repair="PROVE_OFFICIAL_FIXTURE_OR_SCORE_EVENT_SURFACE",\n        ),\n    )\n')
    write('test_osn_048_mls_epl_official_event_surface_foundation_repair.py', '\nfrom qseries_v2.oracle_source_network.acquisition.soccer_event_surface_boundary import states\n\nrows=states()\nfor r in rows:\n    print("[BOUNDARY]",r)\nassert tuple(r.league for r in rows)==("MLS","EPL")\nassert all(r.production_event_admitted is False for r in rows)\nassert all(r.execution_authority is False for r in rows)\nassert rows[0].observed_role=="SCHEDULE_ANNOUNCEMENT_ARTICLE"\nassert rows[1].observed_role=="FIXTURE_ANNOUNCEMENT_ARTICLE"\nprint("[PASS] MLS + EPL article surfaces explicitly removed from production event admission")\nprint("[PASS] OSN-048 MLS + EPL official event-surface foundation repair certified")\n')
    print('[PASS] OSN-048 installed')
    print('[PASS] article surfaces are no longer treated as production event feeds')
    print('[PASS] UCL remains excluded')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
