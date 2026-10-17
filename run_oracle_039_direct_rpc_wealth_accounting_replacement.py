import argparse

from qseries_v2.oracle_execution.oracle_039_direct_rpc_wealth_accounting_replacement import run

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument(
        "--seconds",
        type=float,
        default=300.0,
    )
    a=p.parse_args()

    raise SystemExit(
        run(seconds=a.seconds)
    )
