from pathlib import Path
import ast

ROOT=Path.cwd()

Q87=(
    ROOT/
    "qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qarb_execution_engineering"/
    "qarb_087_two_second_compaction_liquidity_repair.py"
)

TEST=ROOT/"test_sae_004_pumpswap_pool_v2_account_contract.py"

if not Q87.is_file():
    raise RuntimeError("QARB087_SOURCE_MISSING")

src=Q87.read_text(encoding="utf-8")

old="PUMP_FIXED_ACCOUNTS=23"

if old not in src:
    raise RuntimeError(
        "QARB087_OLD_23_ACCOUNT_BOUNDARY_NOT_FOUND"
    )

src=src.replace(
    old,
    "PUMP_FIXED_ACCOUNTS=24",
    1,
)

src=src.replace(
    "# buy / buyExactQuoteIn each have 23 fixed accounts.",
    "# Current physical PumpSwap contract requires 24 accounts; "
    "account 24 preserves pool_v2.",
)

ast.parse(src)

Q87.write_text(
    src,
    encoding="utf-8"
)

TEST_SOURCE=r'''
import base64
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair
    as q
)


class T(unittest.TestCase):

    def test_current_fixed_account_count(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_buy_exact_quote_in_recognized(self):
        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":[
                {
                    "pubkey":
                        "X"+str(i),
                    "isSigner":False,
                    "isWritable":False,
                }
                for i in range(26)
            ],
        }

        self.assertTrue(
            q.recognized_pump_buy(ix)
        )

    def test_pool_v2_account_is_preserved(self):
        accounts=[
            {
                "pubkey":
                    "ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(26)
        ]

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,removed=(
            q.trim_optional_pump_accounts(ix)
        )

        self.assertIsNotNone(trimmed)

        self.assertEqual(
            len(trimmed["accounts"]),
            24
        )

        self.assertEqual(
            removed,
            2
        )

        #
        # Account index 23 = physical
        # account #24. This was previously
        # being stripped by the stale
        # 23-account boundary.
        #
        self.assertEqual(
            trimmed["accounts"][23]["pubkey"],
            "ACCOUNT_23"
        )

    def test_only_accounts_after_24_removed(self):
        accounts=[
            {
                "pubkey":
                    "ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(26)
        ]

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,_=q.trim_optional_pump_accounts(ix)

        kept=[
            x["pubkey"]
            for x in trimmed["accounts"]
        ]

        self.assertIn(
            "ACCOUNT_23",
            kept
        )

        self.assertNotIn(
            "ACCOUNT_24",
            kept
        )

        self.assertNotIn(
            "ACCOUNT_25",
            kept
        )

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

ast.parse(TEST_SOURCE)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8"
)

print("[PASS] SAE-004 PumpSwap pool_v2 account contract installed")
print("[OLD] Pump fixed boundary=23")
print("[NEW] Pump fixed boundary=24")
print("[PRESERVE] physical account #24 / pool_v2 remaining account")
print("[TRIM] only accounts after required 24 may be removed")
print("[SAE-003] exact quote-in pricing unchanged")
print("[SAE-002] chain-truth gate unchanged")
print("[SAE-001] memory-only Meteora unchanged")
print("[BROADCAST] disabled")