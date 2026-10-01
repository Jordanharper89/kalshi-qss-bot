import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad314_case_record_contract_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  a=d["functions"]["attribute_forward_outcomes"]
  price=d["functions"]["_price_for_pair"]
  case_attrs=sorted({x["attribute"] for x in a["attributes"] if x["owner"]=="c"})
  record_attrs=sorted({x["attribute"] for x in a["attributes"] if x["owner"]=="r"})
  price_record_attrs=sorted({x["attribute"] for x in price["attributes"] if x["owner"]=="record"})
  print("[CASE_ATTRIBUTES]",json.dumps(case_attrs))
  print("[RECORD_ATTRIBUTES]",json.dumps(record_attrs))
  print("[PRICE_RECORD_ATTRIBUTES]",json.dumps(price_record_attrs))
  print("[PRICE_DICT_KEYS]",json.dumps(price["dict_keys"],sort_keys=True))
  required={"snapshot_at","horizon_seconds","evidence_observation_ids","pair_address","experience_id","token_address"}
  self.assertTrue(required.issubset(set(case_attrs)),msg="MISSING_EXPECTED_CASE_ATTRIBUTES")
  self.assertIn("observed_at",record_attrs)
  self.assertIn("observation_id",record_attrs)
  print("[PASS] OSI-055C OAD-314 attribute-aware case/record contract audit")
  print("[TRADER] Exact object contract for future-outcome attribution is now explicit")
  print("[SCOPE] Read-only audit; no guessed dictionary contract")

if __name__=="__main__":
 unittest.main()
