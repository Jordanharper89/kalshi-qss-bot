import os,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
 def test_sim_without_key(self):
  a=os.environ.pop("QSB_SOLANA_PRIVATE_KEY",None);b=os.environ.pop("QSB_SOLANA_WALLET",None)
  try:
   kp,user=c.sim_identity();self.assertIsNone(kp);self.assertEqual(user,"MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X")
  finally:
   if a is not None:os.environ["QSB_SOLANA_PRIVATE_KEY"]=a
   if b is not None:os.environ["QSB_SOLANA_WALLET"]=b
  print("[PASS] simulation runs without private key")
 def test_unsigned_sim(self):
  old=c.rpc;seen={}
  def fake(m,p):
   if m=="getBalance":return {"value":1000}
   seen.update(p[1]);return {"err":None,"accounts":[{"lamports":1100}],"unitsConsumed":1,"logs":[]}
  c.rpc=fake
  try:
   x=c.simulate(b"x","MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X",sigverify=False);self.assertFalse(seen["sigVerify"]);self.assertEqual(x["pnl"],100)
  finally:c.rpc=old
  print("[PASS] unsigned atomic simulation uses sigVerify=False")
if __name__=="__main__":unittest.main(verbosity=2)
