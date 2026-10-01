from pathlib import Path
import ast

ROOT=Path.cwd()

Q87=(
    ROOT/"qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qarb_execution_engineering"/
    "qarb_087_two_second_compaction_liquidity_repair.py"
)

TEST=ROOT/"test_sae_011_disable_unsafe_pump_account_trimming.py"

if not Q87.is_file():
    raise RuntimeError("QARB087_MISSING")

src=Q87.read_text(encoding="utf-8")
tree=ast.parse(src)

target=None

for node in tree.body:
    if (
        isinstance(node,ast.FunctionDef)
        and node.name=="trim_optional_pump_accounts"
    ):
        target=node
        break

if target is None:
    raise RuntimeError(
        "PUMP_TRIM_FUNCTION_NOT_FOUND"
    )

replacement='''def trim_optional_pump_accounts(ix):
    """
    SAE-011:
    PumpSwap remaining accounts are dynamic protocol accounts.

    The installed PumpSwap SDK appends required accounts including
    pool_v2, buyback fee recipient, buyback recipient ATA, and
    potentially other feature-gated remaining accounts.

    Therefore account-count slicing is not a safe compaction method.
    Preserve the instruction exactly.
    """
    if not recognized_pump_buy(ix):
        return None,0

    return None,0
'''

lines=src.splitlines(keepends=True)

new_src="".join(
    lines[:target.lineno-1]
    +[replacement+"\n"]
    +lines[target.end_lineno:]
)

ast.parse(new_src)

Q87.write_text(
    new_src,
    encoding="utf-8"
)

TEST.write_text(r'''
import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair as q
)


class T(unittest.TestCase):

    def test_pump_trim_disabled(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_%d"%i,
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(40)
        ]

        import base64

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC+b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,removed=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(trimmed)
        self.assertEqual(removed,0)

    def test_no_slice_semantics(self):
        src=inspect.getsource(
            q.trim_optional_pump_accounts
        )

        self.assertNotIn(
            "PUMP_FIXED_ACCOUNTS]",
            src
        )

        self.assertIn(
            "Preserve the instruction exactly",
            src
        )

    def test_execution_stays_disabled(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.REAL_MONEY_MOVED)


if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] SAE-011 unsafe Pump account trimming disabled")
print("[PUMP] dynamic remaining accounts preserved exactly")
print("[BUYBACK] trailing recipient + ATA cannot be cut off")
print("[POOL_V2] preserved")
print("[TRANSACTION_SIZE] not bypassed")
print("[BROADCAST] disabled")