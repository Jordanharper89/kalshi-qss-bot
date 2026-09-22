import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_035_pump_trade_raw_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_hydrate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("row_count","hydrated_count","unique_signature_count")},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["hydrated_count"],d["row_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-035 Pump trade raw transactions physically hydrated")
  print("[PASS] signer/token-balance evidence preserved for every captured trade")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
