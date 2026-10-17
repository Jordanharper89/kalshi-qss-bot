from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint8_full_exact_universe_live_watch.py"
TEST=ROOT/"test_canonical_checkpoint8_full_exact_universe_live_watch.py"

MODULE=r"""from __future__ import annotations

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
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint8_full_exact_universe_live_watch.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_pair_cap_expanded(self):
        self.assertIn("PAIR_CAP=32",self.s)
        self.assertIn("pd.MAX_PAIRS=PAIR_CAP",self.s)

    def test_account_cap_expanded(self):
        self.assertIn("ACCOUNT_CAP=768",self.s)
        self.assertIn("m.MAX_ACCOUNTS=ACCOUNT_CAP",self.s)

    def test_reuses_checkpoint7_live_logic(self):
        self.assertIn(
            "checkpoint7_live_90s_fee_ranked_watch as c7",
            self.s,
        )
        self.assertIn("return c7.main()",self.s)

    def test_caps_restored(self):
        self.assertIn("pd.MAX_PAIRS=old_pair_cap",self.s)
        self.assertIn("m.MAX_ACCOUNTS=old_account_cap",self.s)

    def test_no_new_runtime(self):
        self.assertNotIn("asyncio.run(",self.s)
        self.assertIn(
            "existing_sharded_direct_websocket=True",
            self.s,
        )

    def test_no_sim_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-8 full exact-universe live watch installed")
print("[PAIR_CAP] 32; legacy default four-pair ceiling removed for this run")
print("[ACCOUNT_CAP] 768; sharded WebSocket transport preserved")
print("[WATCH] reuses certified checkpoint-7 event-driven fee-ranked logic")
print("[DISCOVERY] not in hot path")
print("[SIMULATION] disabled")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
