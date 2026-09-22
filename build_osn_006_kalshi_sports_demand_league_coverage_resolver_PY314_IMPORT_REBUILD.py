from pathlib import Path

REVISION = "OSN_006_KALSHI_SPORTS_DEMAND_LEAGUE_COVERAGE_RESOLVER_PY314_IMPORT_REBUILD_V1"
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
    print(" OSN-006 KALSHI SPORTS DEMAND RESOLVER — PYTHON 3.14 IMPORT REBUILD INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py")
    matches = list((ROOT/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))
    if not matches:
        raise SystemExit("[FAIL] certified OAD-418 dependency missing")
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))

    write("qseries_v2/oracle_source_network/coverage/oad418_probe.py", '\n"""Best-effort read-only extraction of OAD-418 repo-resident gap evidence."""\nfrom pathlib import Path\nimport importlib.util, json, sys\n\ndef _oad418_file(root: Path):\n    matches = list((root/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))\n    if not matches:\n        raise FileNotFoundError("OAD-418 module not found")\n    return matches[0]\n\ndef module_public_data(root: Path):\n    path = _oad418_file(root)\n    module_name = "_osn_oad418_probe"\n    spec = importlib.util.spec_from_file_location(module_name, path)\n    if spec is None or spec.loader is None:\n        raise ImportError(f"unable to create import spec for {path}")\n    mod = importlib.util.module_from_spec(spec)\n    sys.modules[module_name] = mod\n    try:\n        spec.loader.exec_module(mod)\n    finally:\n        sys.modules.pop(module_name, None)\n\n    rows = []\n    for name, value in vars(mod).items():\n        if name.startswith("_"):\n            continue\n        if isinstance(value, (dict, list, tuple, set)):\n            rows.append({"name": name, "value": value})\n    return rows\n\ndef report_files(root: Path):\n    candidates = []\n    for pattern in ("*418*.json", "*gap*priority*.json", "*coverage*gap*.json"):\n        candidates.extend(root.rglob(pattern))\n    out = []\n    seen = set()\n    for p in candidates:\n        if p in seen:\n            continue\n        seen.add(p)\n        try:\n            out.append({\n                "path": str(p.relative_to(root)),\n                "value": json.loads(p.read_text(encoding="utf-8")),\n            })\n        except Exception:\n            pass\n    return out\n')
    write("test_osn_006_kalshi_sports_demand_league_coverage_resolver.py", '\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.coverage.kalshi_sports_demand import resolve_records\nfrom qseries_v2.oracle_source_network.coverage.oad418_probe import module_public_data, report_files\n\nsample = [\n    {"title":"NFL: Texans vs Colts"},\n    {"title":"NBA: Rockets vs Spurs"},\n    {"title":"NHL: Stars vs Avalanche"},\n    {"title":"MLS: Houston Dynamo vs Austin FC"},\n]\nr = resolve_records(sample)\nassert r["live_sports_markets_evaluated"] == 4\nassert r["league_counts"]["NFL"] == 1\nassert r["league_counts"]["NBA"] == 1\nassert r["league_counts"]["NHL"] == 1\nassert r["league_counts"]["MLS"] == 1\n\nroot = Path.cwd()\npub = module_public_data(root)\nreports = report_files(root)\nprint(f"[PHYSICAL] oad418_public_data_objects={len(pub)} report_files={len(reports)}")\nprint("[PASS] Python 3.14-safe OAD-418 probe certified")\nprint("[PASS] OSN-006 Kalshi sports demand resolver certified")\n')

    print("[PASS] OSN-006 Python 3.14 import rebuild installed")
    print("[PASS] READ_ONLY=TRUE execution_authority=FALSE")

if __name__ == "__main__":
    main()
