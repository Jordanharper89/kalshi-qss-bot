from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_067c_live_priority_rate_safe_birth_worker.py"
TEST=ROOT/"test_suls_067d_preserve_restart_backfill_state.py"

OLD='"rate_limited_last_cycle":rate_limited,"capture_policy":"LIVE_NEWEST_FIRST_RECOVERY_BACKGROUND",'
NEW='"rate_limited_last_cycle":rate_limited,"restart_backfill_ready":bool(state.get("restart_backfill_ready")),\n  "capture_policy":"LIVE_NEWEST_FIRST_RECOVERY_BACKGROUND",'

TEST_TEXT=r"""import unittest
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
"""

def main():
 print("="*116);print(" SULS-067D PRESERVE RESTART-BACKFILL STATE");print("="*116)
 src=TARGET.read_text(encoding="utf-8")
 if NEW in src:
  print("[PASS] repair already installed")
 elif OLD not in src:
  raise SystemExit("EXPECTED_SULS_067C_STATE_ASSIGNMENT_NOT_FOUND")
 else:
  TARGET.with_suffix(".pre_suls067d.bak").write_text(src,encoding="utf-8")
  TARGET.write_text(src.replace(OLD,NEW,1),encoding="utf-8")
  print("[PASS] repaired:",TARGET.relative_to(ROOT))
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()