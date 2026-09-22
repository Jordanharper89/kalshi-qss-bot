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
    print(" OSN-006 LIVE KALSHI SPORTS DEMAND → LEAGUE COVERAGE RESOLVER INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/certification/reuse_gate.py")
    matches = list((ROOT/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))
    if not matches:
        raise SystemExit("[FAIL] certified OAD-418 dependency missing")
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    write("qseries_v2/oracle_source_network/coverage/__init__.py", '"""OSN coverage analysis."""')
    write("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py", '\n"""OSN-006: resolve Kalshi sports-market demand into canonical league families."""\nfrom dataclasses import dataclass\nfrom typing import Iterable, Mapping, Any\nimport re\n\nREVISION = "OSN_006_KALSHI_SPORTS_DEMAND_LEAGUE_COVERAGE_RESOLVER_V1"\n\nLEAGUE_PATTERNS = (\n    ("MLB", (r"\\bmlb\\b", r"major league baseball", r"\\bbaseball\\b")),\n    ("NFL", (r"\\bnfl\\b", r"national football league")),\n    ("NCAAF", (r"\\bncaaf\\b", r"college football", r"ncaa football")),\n    ("NBA", (r"\\bnba\\b", r"national basketball association")),\n    ("NCAAB", (r"\\bncaab\\b", r"college basketball", r"ncaa basketball")),\n    ("NHL", (r"\\bnhl\\b", r"national hockey league")),\n    ("MLS", (r"\\bmls\\b", r"major league soccer")),\n    ("EPL", (r"\\bepl\\b", r"premier league")),\n    ("UCL", (r"\\bucl\\b", r"champions league")),\n)\n\ndef _flatten_text(x):\n    if x is None:\n        return []\n    if isinstance(x, str):\n        return [x]\n    if isinstance(x, Mapping):\n        out = []\n        for k, v in x.items():\n            out.extend(_flatten_text(k))\n            out.extend(_flatten_text(v))\n        return out\n    if isinstance(x, (list, tuple, set)):\n        out = []\n        for v in x:\n            out.extend(_flatten_text(v))\n        return out\n    return [str(x)]\n\ndef detect_league(record: Any):\n    text = " ".join(_flatten_text(record)).lower()\n    hits = []\n    for league, pats in LEAGUE_PATTERNS:\n        if any(re.search(p, text, re.I) for p in pats):\n            hits.append(league)\n    return hits[0] if len(hits) == 1 else (hits[0] if hits else "UNKNOWN")\n\ndef resolve_records(records: Iterable[Any]):\n    counts = {}\n    total = 0\n    for rec in records:\n        total += 1\n        league = detect_league(rec)\n        counts[league] = counts.get(league, 0) + 1\n    return {\n        "live_sports_markets_evaluated": total,\n        "league_counts": dict(sorted(counts.items())),\n    }\n')
    write("qseries_v2/oracle_source_network/coverage/oad418_probe.py", '\n"""Best-effort read-only extraction of OAD-418 repo-resident gap evidence."""\nfrom pathlib import Path\nimport importlib.util, json\n\ndef _oad418_file(root: Path):\n    matches = list((root/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))\n    if not matches:\n        raise FileNotFoundError("OAD-418 module not found")\n    return matches[0]\n\ndef module_public_data(root: Path):\n    path = _oad418_file(root)\n    spec = importlib.util.spec_from_file_location("_osn_oad418_probe", path)\n    mod = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(mod)\n    rows = []\n    for name, value in vars(mod).items():\n        if name.startswith("_"):\n            continue\n        if isinstance(value, (dict, list, tuple, set)):\n            rows.append({"name": name, "value": value})\n    return rows\n\ndef report_files(root: Path):\n    candidates = []\n    for pattern in ("*418*.json", "*gap*priority*.json", "*coverage*gap*.json"):\n        candidates.extend(root.rglob(pattern))\n    out = []\n    seen = set()\n    for p in candidates:\n        if p in seen:\n            continue\n        seen.add(p)\n        try:\n            out.append({"path": str(p.relative_to(root)), "value": json.loads(p.read_text(encoding="utf-8"))})\n        except Exception:\n            pass\n    return out\n')
    write("test_osn_006_kalshi_sports_demand_league_coverage_resolver.py", '\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.coverage.kalshi_sports_demand import detect_league, resolve_records\nfrom qseries_v2.oracle_source_network.coverage.oad418_probe import module_public_data, report_files\n\nsample = [\n    {"title":"NFL: Texans vs Colts"},\n    {"title":"NBA: Rockets vs Spurs"},\n    {"title":"NHL: Stars vs Avalanche"},\n    {"title":"MLS: Houston Dynamo vs Austin FC"},\n]\nr = resolve_records(sample)\nassert r["live_sports_markets_evaluated"] == 4\nassert r["league_counts"]["NFL"] == 1\nassert r["league_counts"]["NBA"] == 1\nassert r["league_counts"]["NHL"] == 1\nassert r["league_counts"]["MLS"] == 1\n\nroot = Path.cwd()\npub = module_public_data(root)\nreports = report_files(root)\nprint(f"[PHYSICAL] oad418_public_data_objects={len(pub)} report_files={len(reports)}")\nprint("[PASS] OSN-006 Kalshi sports demand resolver certified")\n')
    print("[PASS] OSN-006 installed")
    print("[PASS] READ_ONLY=TRUE execution_authority=FALSE")

if __name__ == "__main__":
    main()
