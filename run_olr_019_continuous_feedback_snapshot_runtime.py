from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import materialize_feedback_snapshot

def main():
    p=argparse.ArgumentParser();p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args()
    if a.cadence_seconds<=0:raise SystemExit("invalid cadence")
    root=Path.cwd()
    print("="*72,flush=True);print(" OLR-019 CONTINUOUS LEARNED-STATE FEEDBACK SNAPSHOT RUNTIME",flush=True);print("="*72,flush=True)
    cycles=0
    try:
        while True:
            s=materialize_feedback_snapshot(root);cycles+=1
            print(f"[FEEDBACK] cycle={cycles} markets={s.markets} learned_records={s.learned_records} snapshot={s.snapshot_path} execution_authority=FALSE",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
    except KeyboardInterrupt:
        print("\n[STOP] Feedback snapshot runtime stopped by operator.",flush=True);return 0

if __name__=="__main__":raise SystemExit(main())
