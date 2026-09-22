
from pathlib import Path
import argparse,time
from .olr_009_high_coverage_learning_cycle import run_high_coverage_learning_cycle
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--settled-limit",type=int,default=100);p.add_argument("--evidence-limit",type=int,default=3);p.add_argument("--cadence-seconds",type=float,default=15.0);p.add_argument("--once",action="store_true");a=p.parse_args(argv)
    if a.settled_limit<1 or a.evidence_limit<1 or a.cadence_seconds<=0:raise SystemExit("invalid arguments")
    root=Path.cwd();print("="*72,flush=True);print(" OLR-010 HIGH-COVERAGE CONTINUOUS LEARNING RUNTIME",flush=True);print("="*72,flush=True);cycles=0
    try:
        while True:
            s=run_high_coverage_learning_cycle(root,a.settled_limit,a.evidence_limit,lambda x:print(x,flush=True));cycles+=1;print(f"[LEARN] runtime_cycle={cycles} idle={s.idle} learned_total={s.learned_total}",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
    except KeyboardInterrupt:
        print("\\n[STOP] Learning runtime stopped by operator.",flush=True);return 0
