from __future__ import annotations
import argparse
import time
from pathlib import Path

from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import (
    EXECUTION_AUTHORITY,
    PUBLICATION_ALLOWED,
    run as run_prediction,
)
from qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver import run as resolve_full_evidence_outcomes
from qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean import run as run_full_evidence_scoreboard_clean

DEFAULT_CADENCE_SECONDS = 30.0


def verify_boundary():
    if EXECUTION_AUTHORITY is not False:
        raise RuntimeError("execution authority must remain FALSE")
    if PUBLICATION_ALLOWED is not False:
        raise RuntimeError("publication authority must remain FALSE")
    return True


def run_forever(root=None, cadence_seconds=DEFAULT_CADENCE_SECONDS):
    root = Path(root or Path.cwd()).resolve()
    cadence_seconds = float(cadence_seconds)
    if cadence_seconds <= 0:
        raise ValueError("cadence_seconds must be > 0")
    verify_boundary()
    cycle = 0
    while True:
        cycle += 1
        started = time.monotonic()
        print(
            f"[FULL-EVIDENCE LIVE] cycle={cycle} event=PREDICT cadence_seconds={cadence_seconds:.1f} "
            "execution_authority=FALSE publication_allowed=FALSE",
            flush=True,
        )
        run_prediction(root=root)
        resolve_full_evidence_outcomes(root)
        run_full_evidence_scoreboard_clean(root)
        elapsed = max(0.0, time.monotonic() - started)
        time.sleep(max(0.0, cadence_seconds - elapsed))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--cadence-seconds", type=float, default=DEFAULT_CADENCE_SECONDS)
    a = p.parse_args(argv)
    if a.check:
        verify_boundary()
        print("[PASS] full-evidence predictor child boundary verified")
        print("[CADENCE_SECONDS]", a.cadence_seconds)
        print("[EXECUTION/PUBLICATION] FALSE/FALSE")
        return 0
    run_forever(Path.cwd(), a.cadence_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
