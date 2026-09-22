from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback

def main():
    p=argparse.ArgumentParser();p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args()
    if a.cadence_seconds<=0:raise SystemExit("invalid cadence")
    root=Path.cwd()
    print("="*72,flush=True);print(" OLR-029 LIVE REASONING FEEDBACK PROJECTION RUNTIME",flush=True);print("="*72,flush=True)
    cycles=0
    try:
        while True:
            s=materialize_live_reasoning_feedback(root);cycles+=1
            print(f"[CALIBRATION FEEDBACK] cycle={cycles} records={s.calibration_records} markets={s.markets} mature_markets={s.mature_markets} snapshot={s.output_path} execution_authority=FALSE",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
    except KeyboardInterrupt:
        print("\n[STOP] Calibration feedback runtime stopped by operator.",flush=True);return 0

if __name__=="__main__":raise SystemExit(main())
