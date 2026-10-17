import getpass
import os

from qseries_v2.oracle_execution.oracle_016_physical_parity_calibration import (
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
