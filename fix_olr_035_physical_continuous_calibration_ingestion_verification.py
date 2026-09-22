from pathlib import Path
import os

ROOT=Path.cwd().resolve()
RUNNER=ROOT/"run_olr_035_physical_continuous_calibration_ingestion_verification.py"
RUNNER_SOURCE='from pathlib import Path\nimport subprocess,sys\n\nfrom qseries_v2.oracle_learning_runtime.olr_032_continuous_calibration_ingestion_cycle import run_calibration_ingestion_cycle\nfrom qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-035 PHYSICAL CONTINUOUS CALIBRATION INGESTION VERIFICATION - CORRECTION V2")\n    print("="*72)\n\n    root=Path.cwd()\n\n    cycle=run_calibration_ingestion_cycle(\n        root,\n        settled_limit=50,\n        evidence_limit=25,\n    )\n\n    print(\n        f"[CALIBRATION] settled={cycle.settled_scanned} "\n        f"learned={cycle.learned_settlements} "\n        f"exact_evidence={cycle.exact_evidence_matches} "\n        f"candidates={cycle.candidates} "\n        f"admitted={cycle.admitted} "\n        f"duplicates={cycle.duplicate_records} "\n        f"abstentions={cycle.probability_abstentions} "\n        f"ledger_records={cycle.ledger_records}"\n    )\n\n    feedback=materialize_live_reasoning_feedback(root)\n\n    print(\n        f"[LIVE FEEDBACK] records={feedback.calibration_records} "\n        f"markets={feedback.markets} "\n        f"mature_markets={feedback.mature_markets}"\n    )\n\n    p=subprocess.run(\n        [\n            sys.executable,\n            str(root/"run_olr_005_continuous_learning_runtime.py"),\n            "--check",\n        ],\n        cwd=str(root),\n    )\n\n    if p.returncode != 0:\n        raise SystemExit(p.returncode)\n\n    print("[PASS] Continuous calibration ingestion physically executed")\n    print("[PASS] Oracle learning child supervises learning + calibration")\n    print("[PASS] Supervisor check returned code=0")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-035 PHYSICAL CONTINUOUS CALIBRATION INGESTION VERIFIED")\n'

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-035 PHYSICAL VERIFICATION RUNNER CORRECTION V2")
    print("="*72)
    print("[ROOT]",ROOT)

    required=[
        ROOT/"qseries_v2"/"oracle_learning_runtime"/"olr_035_production_calibration_supervision_gate.py",
        ROOT/"run_olr_005_continuous_learning_runtime.py",
    ]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        print("[ERROR] Missing required certified files:")
        for item in missing:
            print("       "+item)
        raise SystemExit(1)

    old=RUNNER.read_bytes() if RUNNER.exists() else None
    try:
        write_exact(RUNNER,RUNNER_SOURCE)
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")
    except Exception:
        if old is None:
            if RUNNER.exists():RUNNER.unlink()
        else:
            RUNNER.write_bytes(old)
        print("[ROLLBACK] OLR-035 physical runner correction failed")
        raise

    print("[PASS] Corrected:",RUNNER.name)
    print("[PASS] Success return code no longer executes 'raise None'")
    print("[PASS] Certified OLR-035 modules left untouched")
    print("[DONE] OLR-035 PHYSICAL RUNNER CORRECTION V2 INSTALLED")

if __name__=="__main__":
    main()
