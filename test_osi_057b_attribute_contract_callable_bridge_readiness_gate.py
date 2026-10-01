import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_057_outcome_callable_bridge_readiness_gate import gate,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  d=gate(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[COMPONENTS]",json.dumps(d["components_present"],sort_keys=True))
  print("[CASE_ATTRIBUTES]",json.dumps(d["case_attributes"]))
  print("[RECORD_ATTRIBUTES]",json.dumps(d["record_attributes"]))
  print("[PRICE_RECORD_ATTRIBUTES]",json.dumps(d["price_record_attributes"]))
  print("[PRICE_DICT_KEYS]",json.dumps(d["price_dict_keys"]))
  print("[CALLABLE_NAMES]",json.dumps(d["callable_names"]))
  print("[CALLABLE_BRIDGE_READY]",d["callable_bridge_ready"])
  if not d["callable_bridge_ready"]:
   self.fail("OAD314_ATTRIBUTE_AWARE_CALLABLE_BRIDGE_NOT_READY")
  print("[PASS] OSI-057B attribute-aware callable bridge readiness gate")
  print("[TRADER] Certified exact OAD-314 case/record contract plus callable availability")
  print("[SCOPE] Readiness only; no real outcome or profitability claim")

if __name__=="__main__":
 unittest.main()
