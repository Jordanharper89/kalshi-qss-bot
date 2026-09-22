from pathlib import Path

REVISION = "OSN_006_KALSHI_SPORTS_DEMAND_STATIC_PROBE_REBUILD_V1"
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
    print(" OSN-006 KALSHI SPORTS DEMAND RESOLVER — STATIC OAD-418 PROBE REBUILD INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/coverage/kalshi_sports_demand.py")
    matches = list((ROOT/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))
    if not matches:
        raise SystemExit("[FAIL] certified OAD-418 dependency missing")
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))

    write("qseries_v2/oracle_source_network/coverage/oad418_probe.py", '\n"""Static, read-only OAD-418 evidence inspection. Never imports or executes OAD-418."""\nfrom pathlib import Path\nimport ast\nimport json\n\ndef _oad418_file(root: Path):\n    matches = list((root/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))\n    if not matches:\n        raise FileNotFoundError("OAD-418 module not found")\n    return matches[0]\n\ndef static_literals(root: Path):\n    path = _oad418_file(root)\n    source = path.read_text(encoding="utf-8")\n    tree = ast.parse(source, filename=str(path))\n    rows = []\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            targets = []\n            value_node = None\n            if isinstance(node, ast.Assign):\n                targets = node.targets\n                value_node = node.value\n            else:\n                targets = [node.target]\n                value_node = node.value\n            for target in targets:\n                if isinstance(target, ast.Name) and not target.id.startswith("_") and value_node is not None:\n                    try:\n                        value = ast.literal_eval(value_node)\n                    except Exception:\n                        continue\n                    if isinstance(value, (dict, list, tuple, set, str, int, float, bool, type(None))):\n                        rows.append({"name": target.id, "value": value})\n    return rows\n\ndef report_files(root: Path):\n    candidates = []\n    for pattern in ("*418*.json", "*gap*priority*.json", "*coverage*gap*.json", "*source*coverage*.json"):\n        candidates.extend(root.rglob(pattern))\n    out = []\n    seen = set()\n    for p in candidates:\n        rp = p.resolve()\n        if rp in seen:\n            continue\n        seen.add(rp)\n        try:\n            out.append({\n                "path": str(p.relative_to(root)),\n                "value": json.loads(p.read_text(encoding="utf-8")),\n            })\n        except Exception:\n            pass\n    return out\n')
    write("test_osn_006_kalshi_sports_demand_league_coverage_resolver.py", '\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.coverage.kalshi_sports_demand import resolve_records\nfrom qseries_v2.oracle_source_network.coverage.oad418_probe import static_literals, report_files\n\nsample = [\n    {"title":"NFL: Texans vs Colts"},\n    {"title":"NBA: Rockets vs Spurs"},\n    {"title":"NHL: Stars vs Avalanche"},\n    {"title":"MLS: Houston Dynamo vs Austin FC"},\n]\nr = resolve_records(sample)\nassert r["live_sports_markets_evaluated"] == 4\nassert r["league_counts"]["NFL"] == 1\nassert r["league_counts"]["NBA"] == 1\nassert r["league_counts"]["NHL"] == 1\nassert r["league_counts"]["MLS"] == 1\n\nroot = Path.cwd()\nliterals = static_literals(root)\nreports = report_files(root)\nprint(f"[PHYSICAL] oad418_static_literals={len(literals)} report_files={len(reports)}")\nprint("[PASS] OAD-418 inspected statically without import/execution")\nprint("[PASS] OSN-006 Kalshi sports demand resolver certified")\n')

    print("[PASS] OSN-006 static-probe rebuild installed")
    print("[PASS] upstream OAD-418 will NOT be imported or executed")
    print("[PASS] READ_ONLY=TRUE execution_authority=FALSE")

if __name__ == "__main__":
    main()
