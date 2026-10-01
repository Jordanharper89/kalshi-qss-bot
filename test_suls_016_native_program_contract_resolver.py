import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_016_native_program_contract_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contracts(self):
  p,d=write(ROOT)
  good=[x for x in d["modules"] if x.get("functions")]
  print("[MODULES]",len(d["modules"]));print("[CALLABLE_MODULES]",len(good))
  for x in good:print("[PROGRAM_MODULE]",x["module"],json.dumps(x["functions"],sort_keys=True))
  if not good:self.fail("NO_PROGRAM_IDENTITY_CALLABLES")
  print("[PASS] SULS-016 native program contract resolver")
if __name__=="__main__":unittest.main()
