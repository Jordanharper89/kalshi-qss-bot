import argparse
from qseries_v2.oracle_execution.oracle_034_positive_only_paper_attack_lane import run
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=300.0)
    a=p.parse_args()
    raise SystemExit(run(seconds=a.seconds))
