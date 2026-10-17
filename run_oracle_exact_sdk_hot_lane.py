import getpass
import os

from qseries_v2.oracle_execution.oracle_018_exact_sdk_hot_lane_cutover import (
    main
)


if __name__=="__main__":

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    raise SystemExit(
        main()
    )
