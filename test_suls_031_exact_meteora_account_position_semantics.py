import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_031_exact_meteora_account_position_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_semantics(self):
  p,d=write(ROOT)
  for r in d["rows"]:
   print("[POSITION_NFT_MINTS]",json.dumps(r["position_nft_mints"]))
   print("[CREATED_ACCOUNTS]",json.dumps(r["created_accounts"],sort_keys=True))
   print("[TRANSFERS]",json.dumps(r["transfers"],sort_keys=True))
   if not r["position_nft_mints"]:self.fail("POSITION_NFT_NOT_IDENTIFIED")
   if not r["transfers"]:self.fail("NO_BIRTH_TRANSFERS")
  print("[PASS] SULS-031 exact Meteora account-position semantics")
if __name__=="__main__":unittest.main()
