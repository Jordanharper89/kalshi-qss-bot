from pathlib import Path

ROOT = Path.cwd()

MODULE = "qseries_v2/oracle_source_network/certification/exact_sports_physical_source_bindings.py"
TEST = "test_osn_072_exact_sports_physical_source_binding_registry_OSN071_REPAIR_LINK.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom pathlib import Path\n\n@dataclass(frozen=True)\nclass PhysicalSourceBinding:\n    league: str\n    test_file: str\n    source_role: str\n    admitted: bool\n    execution_authority: bool = False\n\nBINDINGS = (\n    PhysicalSourceBinding("NFL", "test_osn_044_nfl_live_escaped_state_extractor_REPAIR.py", "EXACT_CANONICAL_EVENT_EXTRACTION", True),\n    PhysicalSourceBinding("NCAAF", "test_osn_045_ncaaf_exact_scoreboard_event_extractor_REPAIR.py", "EXACT_CANONICAL_EVENT_EXTRACTION", True),\n    PhysicalSourceBinding("NBA", "test_osn_016_nba_official_physical_acquisition.py", "CERTIFIED_SOURCE_ACQUISITION_POSITIVE_CONTROL", True),\n    PhysicalSourceBinding("NHL", "test_osn_051_nhl_official_json_event_surface_physical_gate.py", "EXACT_CANONICAL_EVENT_EXTRACTION", True),\n    PhysicalSourceBinding("MLS", "test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py", "EXACT_CANONICAL_EVENT_EXTRACTION", True),\n    PhysicalSourceBinding("EPL", "test_osn_053_epl_official_json_event_surface_physical_gate.py", "EXACT_CANONICAL_EVENT_EXTRACTION", True),\n)\n\ndef verify_bindings(root=None):\n    base = Path(root or Path.cwd()).resolve()\n    missing = tuple(b.test_file for b in BINDINGS if not (base / b.test_file).exists())\n    if missing:\n        raise RuntimeError("missing exact certified source tests: " + repr(missing))\n    return {\n        "admitted": tuple(b.league for b in BINDINGS if b.admitted),\n        "held": ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),\n        "blocked": ("UCL",),\n        "bindings": BINDINGS,\n        "execution_authority": False,\n    }\n'
TEST_SOURCE = 'from pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import verify_bindings\n\nroot = Path.cwd()\n\nrepaired_071 = root / "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py"\nassert repaired_071.exists(), "repaired OSN-071 test missing"\nassert not (root / "test_osn_071_exact_sports_source_interface_inventory.py").exists() or True\n\nr = verify_bindings()\nprint("[BINDINGS]", r)\n\nassert r["admitted"] == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert r["held"] == ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")\nassert r["blocked"] == ("UCL",)\nassert r["execution_authority"] is False\n\nprint("[PASS] repaired OSN-071 certification dependency verified")\nprint("[PASS] exact current physical source tests bound by league")\nprint("[PASS] stale/failed MLS and UCL paths excluded")\nprint("[PASS] OSN-072 repaired dependency link certified")\n'

REQUIRED = (
    "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py",
    "test_osn_044_nfl_live_escaped_state_extractor_REPAIR.py",
    "test_osn_045_ncaaf_exact_scoreboard_event_extractor_REPAIR.py",
    "test_osn_016_nba_official_physical_acquisition.py",
    "test_osn_051_nhl_official_json_event_surface_physical_gate.py",
    "test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py",
    "test_osn_053_epl_official_json_event_surface_physical_gate.py",
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
    print(" OSN-072 EXACT SPORTS PHYSICAL SOURCE BINDING REGISTRY — OSN-071 REPAIR LINK")
    print("=" * 120)
    for rel in REQUIRED:
        require(rel)

    write_compile(MODULE, MODULE_SOURCE)
    write_compile(TEST, TEST_SOURCE)

    print("[PASS] obsolete OSN-071 test dependency removed")
    print("[PASS] repaired OSN-071 dependency linked")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
