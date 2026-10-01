import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_013_native_transaction_envelope_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"]);print("[SOURCE_EXCERPT]");print(d["source_excerpt"])
  if "transaction" not in d["source_excerpt"].lower():self.fail("NO_TRANSACTION_ENVELOPE_LOGIC_VISIBLE")
  print("[PASS] SULS-013 native transaction envelope probe")
if __name__=="__main__":unittest.main()
