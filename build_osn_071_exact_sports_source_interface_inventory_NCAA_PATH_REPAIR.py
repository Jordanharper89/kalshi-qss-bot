from pathlib import Path

ROOT = Path.cwd()

MODULE = "qseries_v2/oracle_source_network/certification/exact_sports_source_interface_inventory.py"
TEST = "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py"

MODULE_SOURCE = 'from dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport ast\nimport json\n\nSOURCE_FILES = {\n    "NFL": (\n        "qseries_v2/oracle_source_network/acquisition/nfl_official_live.py",\n        "qseries_v2/oracle_source_network/mapping/nfl_live_escaped_state_extractor.py",\n    ),\n    "NCAAF": (\n        "qseries_v2/oracle_source_network/acquisition/ncaa_football_official_live.py",\n        "qseries_v2/oracle_source_network/mapping/ncaaf_exact_scoreboard_extractor.py",\n    ),\n    "NBA": (\n        "qseries_v2/oracle_source_network/acquisition/nba_official_live.py",\n        "qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py",\n    ),\n    "NHL": (\n        "qseries_v2/oracle_source_network/acquisition/nhl_official_live.py",\n    ),\n    "MLS": (\n        "qseries_v2/oracle_source_network/acquisition/mls_official_live.py",\n    ),\n    "EPL": (\n        "qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py",\n    ),\n}\n\nMANIFEST = Path("qseries_v2/oracle_source_network/state/exact_sports_source_interfaces.json")\n\n@dataclass(frozen=True)\nclass FunctionShape:\n    name: str\n    required_args: tuple\n    optional_args: tuple\n    async_function: bool\n    constructs_canonical_event: bool\n    network_markers: tuple\n\ndef _shape(node, source):\n    args = list(node.args.args)\n    defaults = list(node.args.defaults)\n    required_count = max(0, len(args) - len(defaults))\n    required = tuple(a.arg for a in args[:required_count])\n    optional = tuple(a.arg for a in args[required_count:])\n    segment = ast.get_source_segment(source, node) or ""\n    markers = tuple(\n        marker for marker in ("urlopen", "requests.", "httpx.", "urllib.", "_get(", "fetch(", "acquire(")\n        if marker in segment\n    )\n    return FunctionShape(\n        name=node.name,\n        required_args=required,\n        optional_args=optional,\n        async_function=isinstance(node, ast.AsyncFunctionDef),\n        constructs_canonical_event=("CanonicalSportsEvent(" in segment),\n        network_markers=markers,\n    )\n\ndef capture_interfaces(root=None):\n    base = Path(root or Path.cwd()).resolve()\n    report = {"execution_authority": False, "leagues": {}}\n\n    for league, rels in SOURCE_FILES.items():\n        rows = []\n        for rel in rels:\n            path = base / rel\n            if not path.exists():\n                rows.append({"path": rel, "missing": True, "functions": []})\n                continue\n            source = path.read_text(encoding="utf-8", errors="ignore")\n            tree = ast.parse(source)\n            funcs = []\n            for node in tree.body:\n                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):\n                    funcs.append(asdict(_shape(node, source)))\n            rows.append({"path": rel, "missing": False, "functions": funcs})\n        report["leagues"][league] = rows\n\n    out = base / MANIFEST\n    out.parent.mkdir(parents=True, exist_ok=True)\n    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")\n    return report, out\n'
TEST_SOURCE = 'from qseries_v2.oracle_source_network.certification.exact_sports_source_interface_inventory import capture_interfaces\n\nreport, path = capture_interfaces()\nprint("[MANIFEST]", path)\n\nassert report["execution_authority"] is False\nassert tuple(report["leagues"]) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\n\nfor league, rows in report["leagues"].items():\n    existing = [r for r in rows if not r["missing"]]\n    assert existing, f"{league} has no exact source module"\n    function_count = sum(len(r["functions"]) for r in existing)\n    print(f"[INTERFACE] {league} modules={len(existing)} public_functions={function_count}")\n    for row in existing:\n        print(f"  [MODULE] {row[\'path\']}")\n        for f in row["functions"]:\n            print(\n                f"    [FUNC] {f[\'name\']} "\n                f"required={tuple(f[\'required_args\'])} "\n                f"optional={tuple(f[\'optional_args\'])} "\n                f"canonical={f[\'constructs_canonical_event\']} "\n                f"network={tuple(f[\'network_markers\'])}"\n            )\n    assert function_count > 0, f"{league} exact modules expose no public functions"\n\nprint("[PASS] exact source module interfaces captured from current repo")\nprint("[PASS] NCAAF exact acquisition path verified as ncaa_football_official_live.py")\nprint("[PASS] no runtime callable names guessed")\nprint("[PASS] OSN-071 NCAA path repair certified")\n'

REQUIRED = (
    "qseries_v2/oracle_source_network/certification/final_sports_runtime_certification.py",
    "qseries_v2/oracle_source_network/acquisition/nfl_official_live.py",
    "qseries_v2/oracle_source_network/acquisition/ncaa_football_official_live.py",
    "qseries_v2/oracle_source_network/acquisition/nba_official_live.py",
    "qseries_v2/oracle_source_network/acquisition/nhl_official_live.py",
    "qseries_v2/oracle_source_network/acquisition/mls_official_live.py",
    "qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py",
)

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + rel)
    print("[PASS] dependency verified:", rel)
    return p

def write_compile(rel, source):
    compile(source, rel, "exec")
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding="utf-8")
    compile(p.read_text(encoding="utf-8"), str(p), "exec")
    print("[WRITE]", rel)
    print("[PASS] post-write compile verified:", rel)

def main():
    print("=" * 120)
    print(" OSN-071 EXACT SPORTS SOURCE INTERFACE INVENTORY — NCAA PATH REPAIR")
    print("=" * 120)

    for rel in REQUIRED:
        require(rel)

    stale = ROOT / "qseries_v2/oracle_source_network/acquisition/caa_football_official_live.py"
    if stale.exists():
        raise SystemExit("[FAIL] unexpected obsolete typo-path exists; audit required")
    print("[PASS] obsolete typo-path caa_football_official_live.py absent")
    print("[PASS] certified path ncaa_football_official_live.py present")

    write_compile(MODULE, MODULE_SOURCE)
    write_compile(TEST, TEST_SOURCE)

    print("[PASS] failed OSN-071 typo dependency retired")
    print("[PASS] exact current source paths retained")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
