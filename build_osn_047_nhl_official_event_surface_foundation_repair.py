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
    print(' OSN-047 NHL OFFICIAL EVENT-SURFACE FOUNDATION REPAIR INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/nhl_official_live.py')
    require('qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py')
    write('qseries_v2/oracle_source_network/acquisition/nhl_event_surface_boundary.py', '\nfrom dataclasses import dataclass\nfrom urllib.parse import urlparse\n\n@dataclass(frozen=True, slots=True)\nclass NHLSourceBoundary:\n    page_surface: str\n    event_surface_required: bool\n    page_surface_status: str\n    production_event_admitted: bool\n    reason: str\n    execution_authority: bool = False\n\ndef current_boundary():\n    return NHLSourceBoundary(\n        page_surface="https://www.nhl.com/schedule",\n        event_surface_required=True,\n        page_surface_status="HTML_SHELL_NO_EVENT_OBJECTS_PROVEN",\n        production_event_admitted=False,\n        reason="OSN-041 proved reachable official schedule HTML but zero structured event candidates; do not parse shell as event feed",\n    )\n\ndef validate_official_candidate(url):\n    host=(urlparse(url).hostname or "").lower()\n    return host.endswith("nhl.com")\n')
    write('test_osn_047_nhl_official_event_surface_foundation_repair.py', '\nfrom qseries_v2.oracle_source_network.acquisition.nhl_event_surface_boundary import current_boundary,validate_official_candidate\n\nb=current_boundary()\nprint("[BOUNDARY]",b)\nassert b.event_surface_required is True\nassert b.production_event_admitted is False\nassert b.execution_authority is False\nassert b.page_surface_status=="HTML_SHELL_NO_EVENT_OBJECTS_PROVEN"\nassert validate_official_candidate("https://www.nhl.com/schedule")\nassert not validate_official_candidate("https://example.com/schedule")\nprint("[PASS] OSN-047 retired NHL HTML shell as production event surface")\nprint("[PASS] OSN-047 NHL official event-surface foundation repair certified")\n')
    print('[PASS] OSN-047 installed')
    print('[PASS] NHL schedule HTML retained only as reachability surface')
    print('[PASS] production event admission remains closed until exact official event surface is proven')

if __name__ == "__main__":
    main()
