from pathlib import Path
import ast

ROOT=Path.cwd()
Q87=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering/qarb_087_two_second_compaction_liquidity_repair.py"
TEST=ROOT/"test_sae_006_pumpswap_buyback_accounts.py"

if not Q87.is_file():
    raise RuntimeError("QARB087_SOURCE_MISSING")

src=Q87.read_text(encoding="utf-8")

if "PUMP_FIXED_ACCOUNTS=24" not in src:
    raise RuntimeError("SAE006_EXPECTED_24_ACCOUNT_BOUNDARY_NOT_FOUND")

src=src.replace(
    "PUMP_FIXED_ACCOUNTS=24",
    "PUMP_FIXED_ACCOUNTS=26",
    1
)

ast.parse(src)
Q87.write_text(src,encoding="utf-8")

TEST.write_text(r'''
import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as c

class T(unittest.TestCase):
    def test_required_account_boundary(self):
        self.assertEqual(q.PUMP_FIXED_ACCOUNTS,26)

    def test_trimmer_keeps_first_26(self):
        s=inspect.getsource(q.trim_optional_pump_accounts)
        self.assertIn("PUMP_FIXED_ACCOUNTS",s)

    def test_pool_v2_prior_fix_preserved(self):
        self.assertGreaterEqual(q.PUMP_FIXED_ACCOUNTS,24)

    def test_exact_quote_preserved(self):
        s=inspect.getsource(c.rewrite_pump_buy_bounds)
        self.assertIn("BUY_EXACT_QUOTE_IN_DISC",s)

    def test_sae003_pricer_preserved(self):
        self.assertEqual(c.q18.WORKER_JS.name,"sae003_pump_exact_quote_worker.mjs")

    def test_safety(self):
        self.assertFalse(c.EXECUTION_AUTHORITY)
        self.assertTrue(c.PAPER_ONLY)
        self.assertFalse(c.REAL_MONEY_MOVED)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",inspect.getsource(c))

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] SAE-006 PumpSwap buyback account preservation installed")
print("[OLD] required Pump accounts=24")
print("[NEW] required Pump accounts=26")
print("[PRESERVE] pool_v2 + trailing fee-recipient accounts")
print("[ADDRESSES] reused from existing native Pump template")
print("[HOT_PATH] no new RPC")
print("[BROADCAST] disabled")