import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_023_pump_create_v2_exact_account_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decoder(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"decoded_count":d["decoded_count"],"certified_count":d["certified_count"]},sort_keys=True))
  for x in d["rows"]:print("[DECODE]",json.dumps({"signature":x["signature"],"mint":x["mint"],"bonding_curve":x["bonding_curve"],"associated_bonding_curve":x["associated_bonding_curve"],"quote_mint":x["quote_mint"],"checks":x["checks"]},sort_keys=True))
  self.assertGreater(d["decoded_count"],0);self.assertEqual(d["decoded_count"],d["certified_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-023 Pump.fun create_v2 exact account decoder certified")
  print("[PASS] exact mint + bonding curve + associated curve resolved from official account order")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
