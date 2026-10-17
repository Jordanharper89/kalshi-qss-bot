from __future__ import annotations

import getpass
import os

from qseries_v2.oracle_execution.oracle_001_live_solana_executor import run


def main():
    print(
        "[ORACLE] LIVE SOLANA EXECUTION"
    )

    print(
        "[OWNER] ORACLE execution_authority=TRUE"
    )

    print(
        "[CAP] exact_per_transaction=0.001000_SOL"
    )

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    os.environ[
        "QSB_LIVE_ARM"
    ]="I_ACCEPT_REAL_MONEY_RISK"

    os.environ[
        "ORACLE_SOLANA_EXECUTION_ARM"
    ]="I_ACCEPT_ORACLE_0_001_SOL_EXECUTION"

    return run(
        seconds=120,
        scan_seconds=2.0
    )


if __name__=="__main__":
    raise SystemExit(main())
