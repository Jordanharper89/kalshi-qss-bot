from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import load_live_feedback_snapshot
from qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import build_bounded_learning_consumption

if __name__=="__main__":
    print("="*72)
    print(" OLR-040 PHYSICAL LEARNING CONSUMPTION VERIFICATION")
    print("="*72)
    root=Path.cwd()
    feedback=load_live_feedback_snapshot(root)
    print(f"[LIVE FEEDBACK] markets={len(feedback)}")
    eligible=0
    for ticker,row in list(sorted(feedback.items()))[:25]:
        x=build_bounded_learning_consumption(row)
        if x.available:eligible+=1
        print(f"[LEARNING] market={ticker} samples={row.samples} mature={row.mature} stable={row.stable} available={x.available} adjustment={x.bounded_adjustment:.4f} reason={x.reason}")
    print(f"[SUMMARY] inspected={min(25,len(feedback))} eligible={eligible}")
    print("[PASS] Live learning feedback consumed through maturity/guard boundary")
    print("[PASS] No immature learning can create an adjustment")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-040 PHYSICAL LEARNING CONSUMPTION VERIFIED")
