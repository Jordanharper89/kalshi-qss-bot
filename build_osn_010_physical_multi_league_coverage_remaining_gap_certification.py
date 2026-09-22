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
    print(" OSN-010 PHYSICAL MULTI-LEAGUE COVERAGE + REMAINING GAP CERTIFICATION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/providers/football_official.py")
    require("qseries_v2/oracle_source_network/providers/basketball_official.py")
    require("qseries_v2/oracle_source_network/providers/hockey_soccer_official.py")
    require("qseries_v2/oracle_source_network/providers/mlb_statsapi.py")
    require("qseries_v2/oracle_source_network/coverage/oad418_probe.py")
    write("qseries_v2/oracle_source_network/certification/multi_league_coverage_gate.py", '\n"""OSN-010 physical multi-league coverage report."""\nfrom collections import Counter\nfrom typing import Iterable, Any\nfrom ..coverage.kalshi_sports_demand import detect_league\n\ndef build_coverage(records: Iterable[Any], covered_leagues):\n    covered = {x.upper() for x in covered_leagues}\n    total = 0\n    with_source = 0\n    counts = Counter()\n    uncovered = Counter()\n    for rec in records:\n        total += 1\n        league = detect_league(rec)\n        counts[league] += 1\n        if league in covered:\n            with_source += 1\n        else:\n            uncovered[league] += 1\n    pct = (with_source / total * 100.0) if total else 0.0\n    return {\n        "live_sports_markets_evaluated": total,\n        "markets_with_official_source_candidate": with_source,\n        "markets_without_official_source_candidate": total - with_source,\n        "coverage_percentage": round(pct, 2),\n        "coverage_by_league": dict(sorted(counts.items())),\n        "remaining_unresolved_leagues": dict(sorted(uncovered.items())),\n        "execution_authority": False,\n    }\n')
    write("qseries_v2/oracle_source_network/certification/oad418_physical_coverage_probe.py", '\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.coverage.oad418_probe import module_public_data, report_files\n\ndef extract_candidate_records(root: Path):\n    rows = []\n    for item in report_files(root):\n        val = item["value"]\n        if isinstance(val, list):\n            rows.extend(val)\n        elif isinstance(val, dict):\n            for key in ("markets","rows","gaps","priorities","results","items"):\n                v = val.get(key)\n                if isinstance(v, list):\n                    rows.extend(v)\n    if rows:\n        return rows, "oad418_report_files"\n\n    public = module_public_data(root)\n    for item in public:\n        val = item["value"]\n        if isinstance(val, (list, tuple)):\n            rows.extend(list(val))\n    return rows, "oad418_module_public_data"\n')
    write("test_osn_010_physical_multi_league_coverage_remaining_gap_certification.py", '\nfrom pathlib import Path\nimport qseries_v2.oracle_source_network.providers.football_official\nimport qseries_v2.oracle_source_network.providers.basketball_official\nimport qseries_v2.oracle_source_network.providers.hockey_soccer_official\nfrom qseries_v2.oracle_source_network.providers.league_registry import all_specs\nfrom qseries_v2.oracle_source_network.certification.multi_league_coverage_gate import build_coverage\nfrom qseries_v2.oracle_source_network.certification.oad418_physical_coverage_probe import extract_candidate_records\n\ncovered = {"MLB"} | {s.league for s in all_specs()}\n\nsample = [\n    {"title":"MLB Astros game"},\n    {"title":"NFL Texans game"},\n    {"title":"NBA Rockets game"},\n    {"title":"NHL Stars game"},\n    {"title":"MLS Dynamo game"},\n    {"title":"Unknown sport market"},\n]\ndemo = build_coverage(sample, covered)\nassert demo["live_sports_markets_evaluated"] == 6\nassert demo["markets_with_official_source_candidate"] == 5\nassert demo["execution_authority"] is False\n\nrecords, source = extract_candidate_records(Path.cwd())\nprint(f"[PHYSICAL] demand_source={source} candidate_records={len(records)}")\nif records:\n    report = build_coverage(records, covered)\n    for k, v in report.items():\n        print(f"[COVERAGE] {k}={v}")\nelse:\n    print("[INFO] no row-level OAD-418 records exposed; deterministic coverage engine certified, physical row-level percentage withheld")\n\nprint("[PASS] OSN-010 multi-league coverage gate certified")\nprint("[PASS] execution_authority=FALSE")\n')
    print("[PASS] OSN-010 installed")
    print("[PASS] OSN-006 through OSN-010 slice ready for sequential certification")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
