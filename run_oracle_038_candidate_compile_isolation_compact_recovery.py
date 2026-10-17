import argparse
from qseries_v2.oracle_execution.oracle_038_candidate_compile_isolation_compact_recovery import run

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=300.0)
    a=p.parse_args()
    raise SystemExit(run(seconds=a.seconds))
