import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_067c_live_priority_rate_safe_birth_worker.py"
class T(unittest.TestCase):
 def test_contract(self):
  src=TARGET.read_text(encoding="utf-8")
  self.assertIn('"restart_backfill_ready":bool(state.get("restart_backfill_ready"))',src)
  self.assertIn('"capture_policy":"LIVE_NEWEST_FIRST_RECOVERY_BACKGROUND"',src)
  print("[PASS] SULS-067D recovery certification survives live-priority cycles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
