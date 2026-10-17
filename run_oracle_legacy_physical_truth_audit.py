import getpass
import os

from qseries_v2.oracle_execution.oracle_009_legacy_vs_physical_truth_audit import (
    run
)


def main():
    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    return run()


if __name__=="__main__":
    raise SystemExit(
        main()
    )
