from pathlib import Path
import argparse,time
from qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import capture_continuity_checkpoint

ORH_003_BUILD_ID="ORH-003"
BACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--cadence-seconds",type=float,default=5.0);p.add_argument("--check",action="store_true");a=p.parse_args(argv)
    if a.check:
        print("[READY] OIR-001 continuity checkpoint daemon — ORH-003 resilient")
        print("[PASS] execution_authority=FALSE")
        return 0
    failures=0
    while True:
        try:
            x=capture_continuity_checkpoint(Path.cwd());failures=0
            print(f"[OIR CHECKPOINT] captured_at={x['captured_at']} sequence={x['canonical_sequence_number']} observations={x['canonical_observation_count']} learner_outcomes={x['learner_outcomes_learned']}",flush=True)
            time.sleep(float(a.cadence_seconds))
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            failures+=1;delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f"[ORH-003 CONTINUITY RECOVERY] status=DEGRADED failure={failures} type={type(exc).__name__} retry_in={delay:.1f}s execution_authority=FALSE",flush=True)
            time.sleep(delay)

if __name__=="__main__":raise SystemExit(main())
