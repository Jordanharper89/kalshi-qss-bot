from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

@dataclass(frozen=True)
class ExactSourceBindingCertification:
    interfaces_captured: bool
    bindings_verified: bool
    physical_cycle_passed: bool
    activation_truth_frozen: bool
    direct_runtime_callable_activation: bool
    admitted: tuple
    held: tuple
    blocked: tuple
    next_required: str
    execution_authority: bool = False

TESTS = (
    ("OSN-071", "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py", 30),
    ("OSN-072", "test_osn_072_exact_sports_physical_source_binding_registry.py", 30),
    ("OSN-073", "test_osn_073_bounded_exact_sports_physical_source_cycle.py", 240),
    ("OSN-074", "test_osn_074_honest_sports_source_activation_registry.py", 30),
)

def _run(base, label, filename, timeout):
    path = base / filename
    if not path.exists():
        raise RuntimeError(f"{label} test missing: {filename}")
    print(f"[RUN] {label}: {filename}", flush=True)
    try:
        p = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(base),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label} timed out after {timeout}s") from exc

    if p.stdout:
        print(p.stdout, end="" if p.stdout.endswith("\n") else "\n")
    if p.stderr:
        print(p.stderr, end="" if p.stderr.endswith("\n") else "\n")
    if p.returncode != 0:
        raise RuntimeError(f"{label} failed rc={p.returncode}")
    print(f"[PASS] {label} passed", flush=True)
    return True

def certify_exact_source_binding(root=None):
    base = Path(root or Path.cwd()).resolve()
    result = {}
    for label, filename, timeout in TESTS:
        result[label] = _run(base, label, filename, timeout)

    return ExactSourceBindingCertification(
        interfaces_captured=result["OSN-071"],
        bindings_verified=result["OSN-072"],
        physical_cycle_passed=result["OSN-073"],
        activation_truth_frozen=result["OSN-074"],
        direct_runtime_callable_activation=False,
        admitted=("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL"),
        held=("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),
        blocked=("UCL",),
        next_required="FREEZE_EXACT_RUNTIME_CALLABLES_FROM_OSN071_MANIFEST_THEN_BIND_TO_OSN066_WORKER",
    )
