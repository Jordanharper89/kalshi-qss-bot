from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class SportsRuntimeCertification:
    persistence_foundation: bool
    scheduler: bool
    checkpoint_after_readback: bool
    gap_backfill: bool
    restart_recovery: bool
    admitted: tuple
    held: tuple
    blocked: tuple
    terminal_dependency: str
    runtime_continuity_ready: bool
    execution_authority: bool = False


TESTS = (
    ("OSN-065", "test_osn_065_final_universal_sports_persistence_CURRENT_BOUNDARY_REBUILD.py", 300),
    ("OSN-066", "test_osn_066_universal_sports_runtime_scheduler.py", 30),
    ("OSN-067", "test_osn_067_sports_checkpoint_after_readback.py", 30),
    ("OSN-068", "test_osn_068_sports_downtime_gap_backfill_planner.py", 30),
    ("OSN-069", "test_osn_069_sports_restart_recovery_physical_gate.py", 120),
)


def _run(root, label, filename, timeout):
    path = root / filename
    if not path.exists():
        raise RuntimeError(f"{label} test missing: {filename}")
    print(f"[RUN] {label}: {filename}", flush=True)
    try:
        p = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(root),
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


def certify_sports_runtime():
    root = Path.cwd().resolve()
    passed = {}
    for label, filename, timeout in TESTS:
        passed[label] = _run(root, label, filename, timeout)

    return SportsRuntimeCertification(
        persistence_foundation=passed["OSN-065"],
        scheduler=passed["OSN-066"],
        checkpoint_after_readback=passed["OSN-067"],
        gap_backfill=passed["OSN-068"],
        restart_recovery=passed["OSN-069"],
        admitted=("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL"),
        held=("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),
        blocked=("UCL",),
        terminal_dependency="NONE",
        runtime_continuity_ready=True,
    )
