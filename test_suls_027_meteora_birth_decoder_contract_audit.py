import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_027_meteora_birth_decoder_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);good=[x for x in d["modules"] if x.get("functions")]
  print("[CALLABLE_MODULES]",len(good))
  for x in d["modules"]:
   print("[MODULE]",x["module"])
   if x.get("functions"):print("[FUNCTIONS]",json.dumps(x["functions"],sort_keys=True))
   if x.get("source_excerpt"):print("[SOURCE_EXCERPT]");print(x["source_excerpt"])
  if not good:self.fail("NO_METEORA_DECODER_CONTRACTS")
  print("[PASS] SULS-027 Meteora birth decoder contract audit")
if __name__=="__main__":unittest.main()
