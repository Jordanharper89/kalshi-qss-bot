import os,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.atomic_crossdex_sim import core as c
MRIYA="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
class T(unittest.TestCase):
 def test_default_sim_payer(self):
  a=os.environ.pop("QSB_SOLANA_WALLET",None)
  b=os.environ.pop("QSB_SOLANA_PRIVATE_KEY",None)
  try:self.assertEqual(c.wallet_pubkey(),MRIYA)
  finally:
   if a is not None:os.environ["QSB_SOLANA_WALLET"]=a
   if b is not None:os.environ["QSB_SOLANA_PRIVATE_KEY"]=b
  print("[PASS] no wallet env required for simulation-only run")
 def test_authority_stays_false(self):
  src=open(c.__file__,encoding="utf-8").read()
  self.assertIn('"execution_authority":False',src)
  self.assertIn('"sent":False',src)
  print("[PASS] execution_authority=FALSE sent=FALSE")
if __name__=="__main__":unittest.main(verbosity=2)
