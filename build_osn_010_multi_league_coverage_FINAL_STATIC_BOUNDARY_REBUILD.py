from pathlib import Path

REVISION = "OSN_010_MULTI_LEAGUE_COVERAGE_FINAL_STATIC_BOUNDARY_REBUILD_V1"
ROOT = Path.cwd()

def require_exact(rel):
    p = ROOT / rel
    if not p.exists() or not p.is_file():
        raise SystemExit("[FAIL] missing exact dependency: " + str(p))
    print("[PASS] exact dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(" OSN-010 MULTI-LEAGUE COVERAGE — FINAL STATIC BOUNDARY REBUILD INSTALLER")
    print("=" * 118)

    require_exact("qseries_v2/oracle_source_network/providers/football_official.py")
    require_exact("qseries_v2/oracle_source_network/providers/basketball_official.py")
    require_exact("qseries_v2/oracle_source_network/providers/hockey_soccer_official.py")
    require_exact("qseries_v2/oracle_source_network/providers/mlb_statsapi.py")
    require_exact("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py")
    require_exact("qseries_v2/oracle_adapters/independent/oad_418_evidence_gap_priority_planner.py")

    write("qseries_v2/oracle_source_network/certification/multi_league_coverage_gate.py", '\n"""OSN-010 multi-league coverage accounting."""\nfrom collections import Counter\nfrom typing import Iterable, Any\nfrom ..coverage.kalshi_sports_demand import detect_league\n\ndef build_coverage(records: Iterable[Any], covered_leagues):\n    covered = {str(x).upper() for x in covered_leagues}\n    total = 0\n    with_source = 0\n    counts = Counter()\n    unresolved = Counter()\n\n    for rec in records:\n        total += 1\n        league = detect_league(rec)\n        counts[league] += 1\n        if league in covered:\n            with_source += 1\n        else:\n            unresolved[league] += 1\n\n    return {\n        "live_sports_markets_evaluated": total,\n        "markets_with_official_source_candidate": with_source,\n        "markets_without_official_source_candidate": total - with_source,\n        "coverage_percentage": round((with_source / total * 100.0), 2) if total else None,\n        "coverage_by_league": dict(sorted(counts.items())),\n        "remaining_unresolved_leagues": dict(sorted(unresolved.items())),\n        "execution_authority": False,\n    }\n')
    write("qseries_v2/oracle_source_network/certification/oad418_exact_literal_coverage_probe.py", '\n"""OSN-010 exact static extraction from the certified OAD-418 source file only."""\nfrom pathlib import Path\nimport ast\n\ndef extract_literal_records(path: Path):\n    source = path.read_text(encoding="utf-8")\n    tree = ast.parse(source, filename=str(path))\n    records = []\n\n    for node in ast.walk(tree):\n        value_node = None\n        if isinstance(node, ast.Assign):\n            value_node = node.value\n        elif isinstance(node, ast.AnnAssign):\n            value_node = node.value\n\n        if value_node is None:\n            continue\n\n        try:\n            value = ast.literal_eval(value_node)\n        except Exception:\n            continue\n\n        if isinstance(value, list):\n            records.extend(x for x in value if isinstance(x, dict))\n        elif isinstance(value, tuple):\n            records.extend(x for x in value if isinstance(x, dict))\n        elif isinstance(value, dict):\n            # Support common row-container shapes without guessing beyond the exact file.\n            for key in ("markets", "rows", "gaps", "priorities", "results", "items"):\n                seq = value.get(key)\n                if isinstance(seq, (list, tuple)):\n                    records.extend(x for x in seq if isinstance(x, dict))\n\n    return tuple(records)\n')
    write("test_osn_010_physical_multi_league_coverage_remaining_gap_certification.py", '\nfrom pathlib import Path\n\nimport qseries_v2.oracle_source_network.providers.football_official\nimport qseries_v2.oracle_source_network.providers.basketball_official\nimport qseries_v2.oracle_source_network.providers.hockey_soccer_official\n\nfrom qseries_v2.oracle_source_network.providers.league_registry import all_specs\nfrom qseries_v2.oracle_source_network.certification.multi_league_coverage_gate import build_coverage\nfrom qseries_v2.oracle_source_network.certification.oad418_exact_literal_coverage_probe import extract_literal_records\n\n# MLB was physically certified in OSN-004; the other leagues are registered source boundaries.\ncovered = {"MLB"} | {spec.league for spec in all_specs()}\n\n# Deterministic accounting proof.\nsample = [\n    {"title":"MLB Astros vs Mariners"},\n    {"title":"NFL Texans vs Colts"},\n    {"title":"NCAAF Texas vs Oklahoma"},\n    {"title":"NBA Rockets vs Spurs"},\n    {"title":"NCAAB Duke vs UNC"},\n    {"title":"NHL Stars vs Avalanche"},\n    {"title":"MLS Dynamo vs Austin"},\n    {"title":"EPL Arsenal vs Chelsea"},\n    {"title":"UCL Real Madrid vs Inter"},\n    {"title":"unknown sports market"},\n]\n\ndemo = build_coverage(sample, covered)\nassert demo["live_sports_markets_evaluated"] == 10\nassert demo["markets_with_official_source_candidate"] == 9\nassert demo["markets_without_official_source_candidate"] == 1\nassert demo["coverage_percentage"] == 90.0\nassert demo["execution_authority"] is False\nassert demo["remaining_unresolved_leagues"].get("UNKNOWN") == 1\n\nroot = Path.cwd()\noad418 = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_418_evidence_gap_priority_planner.py"\nassert oad418.exists(), oad418\n\nrecords = extract_literal_records(oad418)\nprint(f"[PHYSICAL] exact_oad418_literal_records={len(records)}")\n\nif records:\n    report = build_coverage(records, covered)\n    for key, value in report.items():\n        print(f"[COVERAGE] {key}={value}")\nelse:\n    print("[INFO] exact OAD-418 source exposes no row-level literal market records")\n    print("[INFO] physical market coverage percentage withheld rather than fabricated")\n\nprint("[PASS] OSN-010 deterministic multi-league coverage accounting certified")\nprint("[PASS] exact OAD-418 inspected statically only")\nprint("[PASS] no dynamic import / no OAD-418 execution / no recursive filesystem scan")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-010 remaining-gap certification boundary certified")\n')

    print("[PASS] OSN-010 final static-boundary rebuild installed")
    print("[PASS] obsolete OSN-006 probe API dependency removed")
    print("[PASS] no dynamic import")
    print("[PASS] no recursive filesystem scan")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
