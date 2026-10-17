import argparse
from qseries_v2.oracle_execution.oracle_036_hot_path_latency_profile import run
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=300.0)
    a=p.parse_args()
    raise SystemExit(run(seconds=a.seconds))
