import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad314_case_record_contract_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  self.assertEqual(d["function"],"attribute_forward_outcomes")
  print("[SIGNATURE_ARGS]",d["signature_args"])
  print("[DICT_GETS]",json.dumps(d["dict_gets"],sort_keys=True))
  print("[SUBSCRIPTS]",json.dumps(d["subscripts"],sort_keys=True))
  print("[LOOPS]",json.dumps(d["loops"][:12],sort_keys=True))
  print("[CALLS]",json.dumps(d["calls"][:20],sort_keys=True))
  if not d["dict_gets"] and not d["subscripts"]:
   self.fail("NO_OAD314_CASE_RECORD_FIELD_CONTRACT_FOUND")
  print("[PASS] OSI-055B OAD-314 exact case/record contract audit")
  print("[TRADER] Extracts the exact fields OAD-314 expects from candidate cases and temporal records")
  print("[SCOPE] Read-only source audit; no guessed shared-key contract")

if __name__=="__main__":
 unittest.main()
