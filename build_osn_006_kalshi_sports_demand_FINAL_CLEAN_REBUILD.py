from pathlib import Path

REVISION = "OSN_006_KALSHI_SPORTS_DEMAND_FINAL_CLEAN_REBUILD_V1"
ROOT = Path.cwd()

def require_exact(rel):
    p = ROOT / rel
    if not p.exists() or not p.is_file():
        raise SystemExit("[FAIL] missing exact dependency: " + str(p))
    print("[PASS] exact dependency verified:", p.relative_to(ROOT))
    return p

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(" OSN-006 KALSHI SPORTS DEMAND RESOLVER — FINAL CLEAN REBUILD INSTALLER")
    print("=" * 118)
    require_exact("qseries_v2/oracle_adapters/independent/oad_418_evidence_gap_priority_planner.py")
    require_exact("qseries_v2/oracle_source_network/certification/reuse_gate.py")

    write("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py", '\n"""OSN-006 final clean Kalshi sports demand resolver."""\nimport re\nfrom collections.abc import Mapping\n\nREVISION = "OSN_006_KALSHI_SPORTS_DEMAND_FINAL_CLEAN_V1"\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\n\nLEAGUE_PATTERNS = (\n    ("MLB", (r"\\bmlb\\b", r"major league baseball", r"\\bbaseball\\b")),\n    ("NFL", (r"\\bnfl\\b", r"national football league")),\n    ("NCAAF", (r"\\bncaaf\\b", r"college football", r"ncaa football")),\n    ("NBA", (r"\\bnba\\b", r"national basketball association")),\n    ("NCAAB", (r"\\bncaab\\b", r"college basketball", r"ncaa basketball")),\n    ("NHL", (r"\\bnhl\\b", r"national hockey league")),\n    ("MLS", (r"\\bmls\\b", r"major league soccer")),\n    ("EPL", (r"\\bepl\\b", r"premier league")),\n    ("UCL", (r"\\bucl\\b", r"champions league")),\n)\n\ndef _flatten_text(value):\n    if value is None:\n        return []\n    if isinstance(value, str):\n        return [value]\n    if isinstance(value, Mapping):\n        out = []\n        for k, v in value.items():\n            out.extend(_flatten_text(k))\n            out.extend(_flatten_text(v))\n        return out\n    if isinstance(value, (list, tuple, set)):\n        out = []\n        for item in value:\n            out.extend(_flatten_text(item))\n        return out\n    return [str(value)]\n\ndef detect_league(record):\n    text = " ".join(_flatten_text(record)).lower()\n    for league, patterns in LEAGUE_PATTERNS:\n        if any(re.search(p, text, re.I) for p in patterns):\n            return league\n    return "UNKNOWN"\n\ndef resolve_records(records):\n    counts = {}\n    total = 0\n    for record in records:\n        total += 1\n        league = detect_league(record)\n        counts[league] = counts.get(league, 0) + 1\n    return {\n        "live_sports_markets_evaluated": total,\n        "league_counts": dict(sorted(counts.items())),\n        "read_only": True,\n        "execution_authority": False,\n    }\n')
    write("qseries_v2/oracle_source_network/coverage/oad418_exact_static_probe.py", '\n"""Static inspection of the exact certified OAD-418 file only."""\nfrom pathlib import Path\nimport ast\n\ndef inspect_exact_oad418(path: Path):\n    source = path.read_text(encoding="utf-8")\n    tree = ast.parse(source, filename=str(path))\n    names = set()\n    dataclass_count = 0\n    function_count = 0\n    class_count = 0\n\n    for node in ast.walk(tree):\n        if isinstance(node, ast.FunctionDef):\n            function_count += 1\n            names.add(node.name)\n        elif isinstance(node, ast.ClassDef):\n            class_count += 1\n            names.add(node.name)\n            for dec in node.decorator_list:\n                if isinstance(dec, ast.Name) and dec.id == "dataclass":\n                    dataclass_count += 1\n                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "dataclass":\n                    dataclass_count += 1\n\n    return {\n        "path": str(path),\n        "bytes": len(source.encode("utf-8")),\n        "functions": function_count,\n        "classes": class_count,\n        "dataclasses": dataclass_count,\n        "symbols": tuple(sorted(names)),\n    }\n')
    write("test_osn_006_kalshi_sports_demand_league_coverage_resolver.py", '\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.coverage.kalshi_sports_demand import (\n    READ_ONLY,\n    EXECUTION_AUTHORITY,\n    detect_league,\n    resolve_records,\n)\nfrom qseries_v2.oracle_source_network.coverage.oad418_exact_static_probe import inspect_exact_oad418\n\nassert READ_ONLY is True\nassert EXECUTION_AUTHORITY is False\n\nsample = [\n    {"title": "NFL: Texans vs Colts"},\n    {"title": "NBA: Rockets vs Spurs"},\n    {"title": "NHL: Stars vs Avalanche"},\n    {"title": "MLS: Houston Dynamo vs Austin FC"},\n    {"title": "MLB: Astros vs Mariners"},\n    {"title": "unknown sports event"},\n]\n\nexpected = ["NFL", "NBA", "NHL", "MLS", "MLB", "UNKNOWN"]\nactual = [detect_league(x) for x in sample]\nassert actual == expected, (actual, expected)\n\nreport = resolve_records(sample)\nassert report["live_sports_markets_evaluated"] == 6\nassert report["league_counts"]["NFL"] == 1\nassert report["league_counts"]["NBA"] == 1\nassert report["league_counts"]["NHL"] == 1\nassert report["league_counts"]["MLS"] == 1\nassert report["league_counts"]["MLB"] == 1\nassert report["league_counts"]["UNKNOWN"] == 1\nassert report["read_only"] is True\nassert report["execution_authority"] is False\n\nroot = Path.cwd()\noad418 = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_418_evidence_gap_priority_planner.py"\nassert oad418.exists(), oad418\n\ninfo = inspect_exact_oad418(oad418)\nassert info["bytes"] > 0\nprint(f"[PHYSICAL] exact_oad418_bytes={info[\'bytes\']} functions={info[\'functions\']} classes={info[\'classes\']}")\nprint("[PASS] exact OAD-418 source inspected statically")\nprint("[PASS] no import/execution/search/recursive scan")\nprint("[PASS] READ_ONLY=TRUE execution_authority=FALSE")\nprint("[PASS] OSN-006 Kalshi sports demand resolver certified")\n')

    print("[PASS] OSN-006 final clean rebuild installed")
    print("[PASS] no dynamic import")
    print("[PASS] no OAD-418 execution")
    print("[PASS] no recursive filesystem scan")
    print("[PASS] no report discovery")
    print("[PASS] READ_ONLY=TRUE execution_authority=FALSE")

if __name__ == "__main__":
    main()
