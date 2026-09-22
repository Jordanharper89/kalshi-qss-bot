from dataclasses import dataclass
from pathlib import Path
import ast
import subprocess
import sys

@dataclass(frozen=True)
class FinalSportsPersistenceCertification:
    osn060: bool
    osn062_current_boundary: bool
    osn063: bool
    osn064: bool
    single_writer: str
    writer_id: str
    canonicalizer: str
    exact_readback: str
    sports_persistence_ready: bool
    execution_authority: bool = False


def _run_test(root, label, filename, timeout_seconds):
    path = root / filename
    if not path.exists():
        raise RuntimeError(f"{label} current certified test missing: {filename}")

    print(f"[RUN] {label}: {filename}", flush=True)

    try:
        completed = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"{label} certification timed out after {timeout_seconds}s: {filename}"
        ) from exc

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n")

    if completed.returncode != 0:
        raise RuntimeError(
            f"{label} certification failed with exit code {completed.returncode}: {filename}"
        )

    print(f"[PASS] {label} current certified test passed", flush=True)
    return True


def _verify_current_osn062_boundary(root):
    boundary = root / "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
    if not boundary.exists():
        raise RuntimeError("current sports single-writer boundary missing")

    text = boundary.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(text)

    functions = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_functions = {
        "canonicalize",
        "submit",
        "await_commit",
        "exact_readback",
        "readback_count",
    }
    missing = required_functions - functions
    if missing:
        raise RuntimeError(
            "current sports boundary missing required functions: " + repr(sorted(missing))
        )

    if 'WRITER_ID = "oracle.osn.sports"' not in text:
        raise RuntimeError("current sports boundary writer_id marker missing")

    if "submit_observation_batch(" not in text:
        raise RuntimeError("current sports boundary no longer routes through OPH-019 submit")

    if "exact_postgresql_readback(" not in text:
        raise RuntimeError("current sports boundary no longer routes through OAD-068 readback")

    if "PRODUCER" in text:
        raise RuntimeError("obsolete producer-style boundary marker still present")

    print("[OSN062_CURRENT_BOUNDARY] writer_id=oracle.osn.sports")
    print("[PASS] current OSN-062 single-writer contract verified directly")
    print("[PASS] obsolete PRODUCER interface absent")
    return True


def certify_final_sports_persistence():
    root = Path.cwd().resolve()

    osn060 = _run_test(
        root,
        "OSN-060",
        "test_osn_060_final_pre_persistence_sports_event_certification.py",
        90,
    )

    osn062 = _verify_current_osn062_boundary(root)

    osn063 = _run_test(
        root,
        "OSN-063",
        "test_osn_063_sports_single_writer_COMMIT_AWAIT_PHYSICAL_REBUILD.py",
        90,
    )

    osn064 = _run_test(
        root,
        "OSN-064",
        "test_osn_064_sports_persistence_READ_BEFORE_WRITE_IDEMPOTENCY_REBUILD.py",
        90,
    )

    return FinalSportsPersistenceCertification(
        osn060=osn060,
        osn062_current_boundary=osn062,
        osn063=osn063,
        osn064=osn064,
        single_writer="OPH-019",
        writer_id="oracle.osn.sports",
        canonicalizer="OAD-261",
        exact_readback="OAD-068",
        sports_persistence_ready=True,
        execution_authority=False,
    )
