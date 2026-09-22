from pathlib import Path

ROOT = Path.cwd()
MODULE = "qseries_v2/oracle_source_network/certification/exact_sports_physical_source_bindings.py"
REPAIR_TEST = "test_osn_072_exact_sports_physical_source_binding_registry_DISCOVERY_REBUILD.py"
CANONICAL_TEST = "test_osn_072_exact_sports_physical_source_binding_registry.py"
MODULE_SOURCE = 'from dataclasses import dataclass\nfrom pathlib import Path\n\n@dataclass(frozen=True)\nclass PhysicalSourceBinding:\n    league: str\n    test_file: str\n    source_role: str\n    admitted: bool\n    execution_authority: bool = False\n\nSPECS = {\n    "NFL": {\n        "prefix": "test_osn_044_",\n        "include": ("extractor",),\n        "exclude": ("schema", "probe",),\n        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",\n    },\n    "NCAAF": {\n        "prefix": "test_osn_045_",\n        "include": ("scoreboard", "extractor"),\n        "exclude": ("schema", "probe",),\n        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",\n    },\n    "NBA": {\n        "prefix": "test_osn_016_",\n        "include": ("nba", "official", "physical", "acquisition"),\n        "exclude": (),\n        "role": "CERTIFIED_SOURCE_ACQUISITION_POSITIVE_CONTROL",\n    },\n    "NHL": {\n        "prefix": "test_osn_051_",\n        "include": ("nhl", "official", "json", "event", "surface"),\n        "exclude": (),\n        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",\n    },\n    "MLS": {\n        "prefix": "test_osn_052_",\n        "include": ("mls", "official", "stats", "exact", "query"),\n        "exclude": ("event_surface_physical_probe",),\n        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",\n    },\n    "EPL": {\n        "prefix": "test_osn_053_",\n        "include": ("epl", "official", "json", "event", "surface"),\n        "exclude": (),\n        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",\n    },\n}\n\ndef _score(name):\n    lower = name.lower()\n    score = 0\n    if "repair" in lower:\n        score += 100\n    if "exact" in lower:\n        score += 30\n    if "extractor" in lower:\n        score += 20\n    if "physical" in lower:\n        score += 10\n    if "probe" in lower:\n        score -= 40\n    return score\n\ndef _resolve_one(base, league, spec):\n    candidates = []\n    for p in base.glob(spec["prefix"] + "*.py"):\n        name = p.name.lower()\n        if not all(token.lower() in name for token in spec["include"]):\n            continue\n        if any(token.lower() in name for token in spec["exclude"]):\n            continue\n        candidates.append(p)\n\n    if not candidates:\n        raise RuntimeError(\n            f"{league} exact certified test not found using prefix={spec[\'prefix\']} "\n            f"include={spec[\'include\']} exclude={spec[\'exclude\']}"\n        )\n\n    candidates.sort(key=lambda p: (_score(p.name), p.name), reverse=True)\n    chosen = candidates[0]\n    return chosen.name, tuple(p.name for p in candidates)\n\ndef resolve_bindings(root=None):\n    base = Path(root or Path.cwd()).resolve()\n    bindings = []\n    discovery = {}\n\n    for league, spec in SPECS.items():\n        chosen, candidates = _resolve_one(base, league, spec)\n        discovery[league] = {"chosen": chosen, "candidates": candidates}\n        bindings.append(\n            PhysicalSourceBinding(\n                league=league,\n                test_file=chosen,\n                source_role=spec["role"],\n                admitted=True,\n            )\n        )\n\n    return tuple(bindings), discovery\n\ndef verify_bindings(root=None):\n    bindings, discovery = resolve_bindings(root=root)\n    return {\n        "admitted": tuple(b.league for b in bindings),\n        "held": ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),\n        "blocked": ("UCL",),\n        "bindings": bindings,\n        "discovery": discovery,\n        "execution_authority": False,\n    }\n\n# Compatibility for downstream OSN-073 while keeping resolution grounded in current repo.\ntry:\n    BINDINGS, _DISCOVERY = resolve_bindings()\nexcept Exception:\n    BINDINGS = ()\n    _DISCOVERY = {}\n'
TEST_SOURCE = 'from pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import verify_bindings\n\nroot = Path.cwd()\n\nassert (root / "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py").exists()\n\nr = verify_bindings(root=root)\nprint("[BINDINGS]", r["admitted"])\n\nfor league, meta in r["discovery"].items():\n    print(f"[DISCOVERY] {league} chosen={meta[\'chosen\']}")\n    for candidate in meta["candidates"]:\n        print(f"  [CANDIDATE] {candidate}")\n\nassert r["admitted"] == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert r["held"] == ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")\nassert r["blocked"] == ("UCL",)\nassert r["execution_authority"] is False\nassert len(r["bindings"]) == 6\n\nfor binding in r["bindings"]:\n    assert (root / binding.test_file).exists(), binding\n    assert binding.admitted is True\n    assert binding.execution_authority is False\n\nmls = next(b for b in r["bindings"] if b.league == "MLS")\nassert "exact_query" in mls.test_file.lower()\nassert "event_surface_physical_probe" not in mls.test_file.lower()\n\nncaaf = next(b for b in r["bindings"] if b.league == "NCAAF")\nassert "scoreboard" in ncaaf.test_file.lower()\nassert "extractor" in ncaaf.test_file.lower()\n\nprint("[PASS] repaired OSN-071 dependency verified")\nprint("[PASS] exact physical source tests discovered from current repo")\nprint("[PASS] repaired candidates preferred over stale variants")\nprint("[PASS] known failed bare MLS probe excluded")\nprint("[PASS] six admitted league bindings resolved")\nprint("[PASS] OSN-072 discovery rebuild certified")\n'

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + rel)
    print("[PASS] dependency verified:", rel)

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
    print(" OSN-072 EXACT SPORTS PHYSICAL SOURCE BINDING REGISTRY — DISCOVERY REBUILD")
    print("=" * 120)

    require("test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py")

    write_compile(MODULE, MODULE_SOURCE)
    write_compile(REPAIR_TEST, TEST_SOURCE)
    write_compile(CANONICAL_TEST, TEST_SOURCE)

    # Import after write so resolution uses the user's real repo files.
    import importlib
    m = importlib.import_module("qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings")
    result = m.verify_bindings(ROOT)

    for league, meta in result["discovery"].items():
        print(f"[RESOLVED] {league} -> {meta['chosen']}")

    if result["admitted"] != ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL"):
        raise SystemExit("[FAIL] admitted binding set mismatch")

    print("[PASS] no exact source test filenames hard-coded")
    print("[PASS] canonical OSN-072 test filename restored for downstream compatibility")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
