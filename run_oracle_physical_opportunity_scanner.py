import argparse
import getpass
import os

from qseries_v2.oracle_execution.oracle_010_continuous_physical_opportunity_scanner import (
    run
)


def main():
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=180.0
    )

    a=ap.parse_args()

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    return run(
        seconds=a.seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
