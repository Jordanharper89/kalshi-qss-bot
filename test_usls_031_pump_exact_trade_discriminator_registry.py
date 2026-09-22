import hashlib,json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_031_pump_exact_trade_discriminator_registry import write,classify
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  checks={}
  for name in ("buy","sell","buy_exact_sol_in"):
   raw=hashlib.sha256(("global:"+name).encode()).digest()[:8]
   # local tiny base58 encoder for deterministic fixture
   n=int.from_bytes(raw,"big");alpha="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";s=""
   while n:n,r=divmod(n,58);s=alpha[r]+s
   x=classify(s or "1");checks[name]=x["side"]
  print("[STATE]",json.dumps({"registry":d["registry"],"fixture_sides":checks},sort_keys=True))
  self.assertEqual(checks["buy"],"BUY");self.assertEqual(checks["sell"],"SELL")
  self.assertEqual(checks["buy_exact_sol_in"],"BUY")
  self.assertEqual(classify("1")["side"],"UNKNOWN_TRADE_TYPE")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-031 Pump exact trade discriminator registry certified")
  print("[PASS] unknown Pump instructions are retained, never guessed into BUY/SELL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
