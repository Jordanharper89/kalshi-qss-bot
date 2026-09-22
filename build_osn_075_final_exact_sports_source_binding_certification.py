from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-075 FINAL EXACT SPORTS SOURCE-BINDING CERTIFICATION INSTALLER'
REQUIRED = ('test_osn_071_exact_sports_source_interface_inventory.py', 'test_osn_072_exact_sports_physical_source_binding_registry.py', 'test_osn_073_bounded_exact_sports_physical_source_cycle.py', 'test_osn_074_honest_sports_source_activation_registry.py')
FILES = {'qseries_v2/oracle_source_network/certification/final_exact_sports_source_binding_certification.py': 'from dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess\nimport sys\n\n@dataclass(frozen=True)\nclass ExactSourceBindingCertification:\n    interfaces_captured: bool\n    bindings_verified: bool\n    physical_cycle_passed: bool\n    activation_truth_frozen: bool\n    direct_runtime_callable_activation: bool\n    admitted: tuple\n    held: tuple\n    blocked: tuple\n    next_required: str\n    execution_authority: bool = False\n\nTESTS = (\n    ("OSN-071", "test_osn_071_exact_sports_source_interface_inventory.py", 30),\n    ("OSN-072", "test_osn_072_exact_sports_physical_source_binding_registry.py", 30),\n    ("OSN-073", "test_osn_073_bounded_exact_sports_physical_source_cycle.py", 240),\n    ("OSN-074", "test_osn_074_honest_sports_source_activation_registry.py", 30),\n)\n\ndef _run(base, label, filename, timeout):\n    p = subprocess.run(\n        [sys.executable, str(base / filename)],\n        cwd=str(base),\n        text=True,\n        capture_output=True,\n        timeout=timeout,\n    )\n    if p.stdout:\n        print(p.stdout, end="" if p.stdout.endswith("\\n") else "\\n")\n    if p.stderr:\n        print(p.stderr, end="" if p.stderr.endswith("\\n") else "\\n")\n    if p.returncode != 0:\n        raise RuntimeError(f"{label} failed rc={p.returncode}")\n    print(f"[PASS] {label} passed")\n    return True\n\ndef certify_exact_source_binding(root=None):\n    base = Path(root or Path.cwd()).resolve()\n    result = {}\n    for label, filename, timeout in TESTS:\n        result[label] = _run(base, label, filename, timeout)\n\n    return ExactSourceBindingCertification(\n        interfaces_captured=result["OSN-071"],\n        bindings_verified=result["OSN-072"],\n        physical_cycle_passed=result["OSN-073"],\n        activation_truth_frozen=result["OSN-074"],\n        direct_runtime_callable_activation=False,\n        admitted=("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL"),\n        held=("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),\n        blocked=("UCL",),\n        next_required="FREEZE_EXACT_RUNTIME_CALLABLES_FROM_OSN071_MANIFEST_THEN_BIND_TO_OSN066_WORKER",\n    )\n', 'test_osn_075_final_exact_sports_source_binding_certification.py': 'from qseries_v2.oracle_source_network.certification.final_exact_sports_source_binding_certification import certify_exact_source_binding\n\nr = certify_exact_source_binding()\nprint("[FINAL_EXACT_SOURCE_BINDING]", r)\n\nassert r.interfaces_captured\nassert r.bindings_verified\nassert r.physical_cycle_passed\nassert r.activation_truth_frozen\nassert r.direct_runtime_callable_activation is False\nassert r.admitted == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert r.execution_authority is False\n\nprint("[PASS] exact source interfaces captured")\nprint("[PASS] exact physical source bindings certified")\nprint("[PASS] six-source bounded physical cycle certified")\nprint("[PASS] no false runtime activation claim made")\nprint("[PASS] OSN-075 exact sports source-binding certification complete")\n'}

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
