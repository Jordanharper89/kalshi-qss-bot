from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import time

from qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import BINDINGS

@dataclass(frozen=True)
class SourceCycleRow:
    league: str
    passed: bool
    returncode: int
    elapsed_seconds: float
    event_lines: int
    physical_lines: int
    execution_authority: bool = False

def run_source_cycle(root=None, per_source_timeout=35):
    base = Path(root or Path.cwd()).resolve()
    rows = []

    for binding in BINDINGS:
        path = base / binding.test_file
        started = time.monotonic()
        try:
            p = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(base),
                text=True,
                capture_output=True,
                timeout=float(per_source_timeout),
            )
            stdout = p.stdout or ""
            stderr = p.stderr or ""
            if stdout:
                print(stdout, end="" if stdout.endswith("\n") else "\n")
            if stderr:
                print(stderr, end="" if stderr.endswith("\n") else "\n")
            passed = p.returncode == 0
            rc = p.returncode
        except subprocess.TimeoutExpired:
            stdout = ""
            passed = False
            rc = 124

        elapsed = round(time.monotonic() - started, 3)
        event_lines = sum(1 for line in stdout.splitlines() if line.startswith("[EVENT]"))
        physical_lines = sum(1 for line in stdout.splitlines() if line.startswith("[PHYSICAL]"))
        row = SourceCycleRow(binding.league, passed, rc, elapsed, event_lines, physical_lines)
        print("[SOURCE_CYCLE]", row)
        rows.append(row)

    return tuple(rows)
