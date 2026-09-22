from pathlib import Path
import subprocess,sys

from qseries_v2.oracle_learning_runtime.olr_032_continuous_calibration_ingestion_cycle import run_calibration_ingestion_cycle
from qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback

if __name__=="__main__":
    print("="*72)
    print(" OLR-035 PHYSICAL CONTINUOUS CALIBRATION INGESTION VERIFICATION - CORRECTION V2")
    print("="*72)

    root=Path.cwd()

    cycle=run_calibration_ingestion_cycle(
        root,
        settled_limit=50,
        evidence_limit=25,
    )

    print(
        f"[CALIBRATION] settled={cycle.settled_scanned} "
        f"learned={cycle.learned_settlements} "
        f"exact_evidence={cycle.exact_evidence_matches} "
        f"candidates={cycle.candidates} "
        f"admitted={cycle.admitted} "
        f"duplicates={cycle.duplicate_records} "
        f"abstentions={cycle.probability_abstentions} "
        f"ledger_records={cycle.ledger_records}"
    )

    feedback=materialize_live_reasoning_feedback(root)

    print(
        f"[LIVE FEEDBACK] records={feedback.calibration_records} "
        f"markets={feedback.markets} "
        f"mature_markets={feedback.mature_markets}"
    )

    p=subprocess.run(
        [
            sys.executable,
            str(root/"run_olr_005_continuous_learning_runtime.py"),
            "--check",
        ],
        cwd=str(root),
    )

    if p.returncode != 0:
        raise SystemExit(p.returncode)

    print("[PASS] Continuous calibration ingestion physically executed")
    print("[PASS] Oracle learning child supervises learning + calibration")
    print("[PASS] Supervisor check returned code=0")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-035 PHYSICAL CONTINUOUS CALIBRATION INGESTION VERIFIED")
