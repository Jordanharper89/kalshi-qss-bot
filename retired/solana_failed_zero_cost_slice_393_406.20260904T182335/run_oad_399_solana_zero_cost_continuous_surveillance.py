from __future__ import annotations
import argparse
from qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker import run_zero_cost_continuous_surveillance

def progress(*a,**k):
    print("[SOLANA]",*a)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cycles",type=int,default=3)
    args=ap.parse_args()
    x=run_zero_cost_continuous_surveillance(max_cycles=args.cycles,progress=progress)
    print("[RESULT]",x)

if __name__=="__main__":
    main()