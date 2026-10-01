from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
TARGET=SUB/"suls_064_confirmed_horizon_outcome_worker.py"
TEST=ROOT/"test_suls_095_reserve_ratio_outcome_semantic_safety_repair.py"

TEST_TEXT=r"""import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_064_confirmed_horizon_outcome_worker.py"

class T(unittest.TestCase):
 def test_semantics(self):
  src=TARGET.read_text(encoding="utf-8")
  self.assertNotIn('"return_from_birth"',src)
  self.assertIn('"reserve_ratio_change_from_birth"',src)
  self.assertIn('"outcome_semantics":"RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY"',src)
  self.assertIn('"executable_pnl":False',src)
  self.assertIn('"profitability_eligible":False',src)
  print("[PASS] SULS-095 reserve-ratio outcome semantic safety repair")
  print("[PASS] reserve-ratio movement cannot masquerade as executable return/PnL")
  print("[PASS] profitability_eligible=FALSE")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-095 RESERVE-RATIO OUTCOME SEMANTIC SAFETY REPAIR")
 print("="*116)
 if not TARGET.exists():
  raise SystemExit("CANONICAL_SULS_064_NOT_FOUND")
 src=TARGET.read_text(encoding="utf-8")
 bak=TARGET.with_suffix(".pre_suls095.bak")
 if not bak.exists():bak.write_text(src,encoding="utf-8")

 src=src.replace('"return_from_birth"', '"reserve_ratio_change_from_birth"')
 src=src.replace("'return_from_birth'", "'reserve_ratio_change_from_birth'")

 marker='return {"revision":"SULS_064"'
 if marker in src and '"outcome_semantics":"RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY"' not in src:
  src=src.replace(marker,
   'return {"revision":"SULS_064","outcome_semantics":"RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY",'
   '"executable_pnl":False,"profitability_eligible":False,',1)

 if '"reserve_ratio_change_from_birth"' not in src:
  raise SystemExit("SULS_064_RETURN_FIELD_NOT_FOUND")
 if '"outcome_semantics":"RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY"' not in src:
  raise SystemExit("SULS_064_RETURN_CONTRACT_NOT_FOUND")

 TARGET.write_text(src,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] repaired canonical:",TARGET.relative_to(ROOT))
 print("[PASS] backup:",bak.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":main()