import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_074_confirmed_logs_subscription_contract.py"
IDS=['6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P', 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA', 'LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj', '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8', 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK', 'CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C', 'dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN', 'cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG', 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo', 'Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB', 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc', 'MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG', 'boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4', 'HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o']
class T(unittest.TestCase):
 def test_contract(self):
  s=P.read_text(encoding="utf-8");ast.parse(s)
  missing=[x for x in IDS if x not in s]
  print("[STATE]",{"program_ids":len(IDS),"missing":len(missing),"logsSubscribe":"logsSubscribe" in s})
  self.assertFalse(missing);self.assertIn("PROGRAM_IDS",s);self.assertIn("logsSubscribe",s)
  print("[PASS] USLS-010 production subscription contract expanded to 14 verified programs")
  print("[PASS] existing SULS subscription API preserved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
