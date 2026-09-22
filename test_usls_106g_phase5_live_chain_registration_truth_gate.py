import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106g_phase5_live_chain_registration_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"birth_chain_top_level_registered":d["birth_chain_top_level_registered"],
   "trade_modules_top_level_registered":d["trade_modules_top_level_registered"],"finding":d["finding"]},sort_keys=True))
  for x in d["birth_chain"]:print("[BIRTH_CHAIN]",json.dumps(x,sort_keys=True))
  for x in d["trade_modules"]:print("[TRADE_MODULE]",json.dumps(x,sort_keys=True))
  self.assertTrue(all(x["exists"] for x in d["birth_chain"]),"BIRTH_CHAIN_MODULE_MISSING")
  self.assertTrue(all(x["exists"] for x in d["trade_modules"]),"TRADE_MODULE_MISSING")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106G live-chain registration truth gate")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
