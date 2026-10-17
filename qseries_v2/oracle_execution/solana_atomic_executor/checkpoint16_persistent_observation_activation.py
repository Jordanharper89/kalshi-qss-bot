from __future__ import annotations
import argparse

from qseries_v2.oracle_execution.solana_atomic_executor import (
    checkpoint15_cheapest_legal_fee_signed_simulation as c15
)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError("CHECKPOINT16_SECONDS_MUST_BE_POSITIVE")

    c15.SECONDS=float(args.seconds)

    print(
        "[CHECKPOINT16_ACTIVATION] "
        "persistent_multi_pool=True "
        "cheapest_legal_fee=True "
        "signed_sim_positive_only=True "
        "seconds=%.0f broadcast=False"
        %c15.SECONDS,
        flush=True,
    )

    return c15.main()

if __name__=="__main__":
    raise SystemExit(main())
