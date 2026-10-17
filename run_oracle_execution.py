from __future__ import annotations

import argparse
import getpass
import os

from qseries_v2.oracle_execution.oracle_003_unified_physical_execution_engine import run


def main():
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--paper",
        action="store_true"
    )

    ap.add_argument(
        "--seconds",
        type=int,
        default=120
    )

    a=ap.parse_args()

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    mode=(
        "PAPER"
        if a.paper
        else "LIVE"
    )

    if mode=="LIVE":
        os.environ[
            "QSB_LIVE_ARM"
        ]="I_ACCEPT_REAL_MONEY_RISK"

        os.environ[
            "ORACLE_SOLANA_EXECUTION_ARM"
        ]="I_ACCEPT_ORACLE_0_001_SOL_EXECUTION"

    return run(
        mode=mode,
        seconds=a.seconds
    )


if __name__=="__main__":
    raise SystemExit(main())
