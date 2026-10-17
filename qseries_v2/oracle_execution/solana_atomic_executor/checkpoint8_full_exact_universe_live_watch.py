from __future__ import annotations

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m


PAIR_CAP=32
ACCOUNT_CAP=768
SECONDS=90.0


def main():
    old_pair_cap=pd.MAX_PAIRS
    old_account_cap=m.MAX_ACCOUNTS

    pd.MAX_PAIRS=PAIR_CAP
    m.MAX_ACCOUNTS=ACCOUNT_CAP

    print(
        "[CHECKPOINT8_COVERAGE_EXPANSION] "
        "pair_cap=%d account_cap=%d"
        %(PAIR_CAP,ACCOUNT_CAP),
        flush=True,
    )
    print(
        "[CHECKPOINT8_PURPOSE] "
        "remove_legacy_four_pair_ceiling=True",
        flush=True,
    )
    print(
        "[CHECKPOINT8_TRANSPORT] "
        "existing_sharded_direct_websocket=True",
        flush=True,
    )
    print(
        "[CHECKPOINT8_HOT_PATH] "
        "discovery=False replenishment_only=True",
        flush=True,
    )
    print("[SIMULATION] disabled",flush=True)
    print("[BROADCAST] disabled",flush=True)

    try:
        return c7.main()
    finally:
        pd.MAX_PAIRS=old_pair_cap
        m.MAX_ACCOUNTS=old_account_cap


if __name__=="__main__":
    raise SystemExit(main())
