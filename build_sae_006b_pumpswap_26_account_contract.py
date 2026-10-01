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

TEST=ROOT/"test_sae_006b_pumpswap_26_account_contract.py"

if not Q87.is_file():
    raise RuntimeError("QARB087_SOURCE_MISSING")

src=Q87.read_text(encoding="utf-8")
tree=ast.parse(src)

target=None
old_value=None

for node in tree.body:
    if not isinstance(node,ast.Assign):
        continue

    for t in node.targets:
        if (
            isinstance(t,ast.Name)
            and t.id=="PUMP_FIXED_ACCOUNTS"
        ):
            target=node

            if isinstance(node.value,ast.Constant):
                old_value=node.value.value

            break

    if target is not None:
        break

if target is None:
    raise RuntimeError(
        "PUMP_FIXED_ACCOUNTS_ASSIGNMENT_NOT_FOUND"
    )

lines=src.splitlines(keepends=True)

replacement="PUMP_FIXED_ACCOUNTS=26\n"

new_src="".join(
    lines[:target.lineno-1]
    +[replacement]
    +lines[target.end_lineno:]
)

ast.parse(new_src)

Q87.write_text(
    new_src,
    encoding="utf-8"
)

TEST_SOURCE=r'''
import base64
import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair
    as q
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as c
)


class T(unittest.TestCase):

    def test_26_account_contract(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            26
        )

    def test_exact_quote_buy_recognized(self):
        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":[],
        }

        self.assertTrue(
            q.recognized_pump_buy(ix)
        )

    def test_first_26_preserved(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(28)
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
            26
        )

        self.assertEqual(
            removed,
            2
        )

        self.assertEqual(
            trimmed["accounts"][23]["pubkey"],
            "ACCOUNT_23"
        )

        self.assertEqual(
            trimmed["accounts"][24]["pubkey"],
            "ACCOUNT_24"
        )

        self.assertEqual(
            trimmed["accounts"][25]["pubkey"],
            "ACCOUNT_25"
        )

    def test_exact_26_not_trimmed(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_"+str(i),
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

        self.assertIsNone(trimmed)
        self.assertEqual(removed,0)

    def test_sae003_preserved(self):
        self.assertEqual(
            c.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_size_curve_preserved(self):
        src=inspect.getsource(
            c.exact_best
        )

        for size in (
            "0.001",
            "0.010",
            "0.025",
            "0.050",
            "0.100",
            "0.180",
            "0.280",
            "0.500",
            "1.000",
            "1.400",
        ):
            self.assertIn(size,src)

    def test_safety(self):
        self.assertFalse(
            c.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            c.PAPER_ONLY
        )

        self.assertFalse(
            c.REAL_MONEY_MOVED
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            inspect.getsource(c)
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

ast.parse(TEST_SOURCE)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8"
)

print(
    "[PASS] SAE-006B PumpSwap 26-account contract installed"
)

print(
    "[OLD_BOUNDARY] %s"%old_value
)

print(
    "[NEW_BOUNDARY] 26"
)

print(
    "[PRESERVE] accounts 1-26"
)

print(
    "[TARGET] eliminate 6058 BuybackFeeRecipientMissing"
)

print(
    "[SAE-003] exact quote-in pricing preserved"
)

print(
    "[SAE-005E] dynamic size curve preserved"
)

print(
    "[BROADCAST] disabled"
)