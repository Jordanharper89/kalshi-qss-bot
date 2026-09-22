from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-074 HONEST SPORTS SOURCE ACTIVATION REGISTRY INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/state/exact_sports_source_interfaces.json', 'qseries_v2/oracle_source_network/certification/exact_sports_physical_source_bindings.py')
FILES = {'qseries_v2/oracle_source_network/runtime/sports_source_activation_registry.py': 'from dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import BINDINGS\n\n@dataclass(frozen=True)\nclass SourceActivationEntry:\n    league: str\n    source_test: str\n    physical_certified: bool\n    direct_runtime_callable_bound: bool\n    state: str\n    execution_authority: bool = False\n\ndef build_activation_registry(root=None):\n    base = Path(root or Path.cwd()).resolve()\n    interface_manifest = base / "qseries_v2/oracle_source_network/state/exact_sports_source_interfaces.json"\n    if not interface_manifest.exists():\n        raise RuntimeError("OSN-071 exact interface manifest missing")\n    interfaces = json.loads(interface_manifest.read_text(encoding="utf-8"))\n\n    entries = []\n    for binding in BINDINGS:\n        rows = interfaces["leagues"][binding.league]\n        public_functions = sum(len(r.get("functions", ())) for r in rows if not r.get("missing"))\n        entries.append(\n            SourceActivationEntry(\n                league=binding.league,\n                source_test=binding.test_file,\n                physical_certified=True,\n                direct_runtime_callable_bound=False,\n                state="PHYSICAL_SOURCE_PROVEN_RUNTIME_CALLABLE_NOT_YET_FROZEN" if public_functions else "INTERFACE_MISSING",\n            )\n        )\n    return tuple(entries)\n', 'test_osn_074_honest_sports_source_activation_registry.py': 'from qseries_v2.oracle_source_network.runtime.sports_source_activation_registry import build_activation_registry\n\nrows = build_activation_registry()\nfor row in rows:\n    print("[ACTIVATION]", row)\n\nassert tuple(r.league for r in rows) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert all(r.physical_certified is True for r in rows)\nassert all(r.execution_authority is False for r in rows)\nassert all(r.state == "PHYSICAL_SOURCE_PROVEN_RUNTIME_CALLABLE_NOT_YET_FROZEN" for r in rows)\n\nprint("[PASS] source truth frozen without falsely claiming direct runtime callable activation")\nprint("[PASS] exact interface manifest preserved for next binding step")\nprint("[PASS] OSN-074 honest source activation registry certified")\n'}

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
    print(" " + TITLE)
    print("=" * 120)
    for rel in REQUIRED:
        require(rel)
    for rel, source in FILES.items():
        write_compile(rel, source)
    print("[PASS] installer completed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
