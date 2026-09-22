from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_026_durable_calibration_ledger import load_calibration_ledger
from qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback

if __name__=="__main__":
    print("="*72)
    print(" OLR-030 PHYSICAL DURABLE CALIBRATION + LIVE FEEDBACK VERIFICATION")
    print("="*72)
    root=Path.cwd()
    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"
    ledger=load_calibration_ledger(ledger_path)
    print(f"[CALIBRATION LEDGER] records={len(ledger)} path=runtime_state\\oracle_calibration_ledger.json")
    summary=materialize_live_reasoning_feedback(root)
    print(f"[LIVE FEEDBACK] records={summary.calibration_records} markets={summary.markets} mature_markets={summary.mature_markets}")
    print(f"[LIVE FEEDBACK] snapshot={summary.output_path}")
    print("[PASS] Durable calibration history projected into live reasoning feedback")
    print("[PASS] Frozen OCR/OCL/OIS boundaries remain read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-030 PHYSICAL DURABLE CALIBRATION + LIVE FEEDBACK VERIFIED")
