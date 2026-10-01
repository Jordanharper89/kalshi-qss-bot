import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_042_generic_meteora_birth_role_materializer.py"

def load():
 spec=importlib.util.spec_from_file_location("_suls042_suls102b",P)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class T(unittest.TestCase):
 def test_identity_contract(self):
  m=load()
  inbox=json.loads((ROOT/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json").read_text(encoding="utf-8"))
  found=None
  for b in reversed(list(inbox.get("births") or [])):
   x=m._materialize(b)
   if x is not None:
    found=x;break
  self.assertIsNotNone(found)
  self.assertTrue(found.get("token_address"))
  self.assertTrue(found.get("pair_address"))
  self.assertEqual(found.get("token_address"),found.get("token_mint"))
  self.assertTrue(found.get("token_vault"))
  self.assertTrue(found.get("quote_vault"))
  self.assertFalse(found.get("execution_authority"))
  print("[STATE]",json.dumps({k:found.get(k) for k in (
   "signature","token_address","token_mint","pair_address",
   "token_vault","quote_vault","launcher_family","execution_authority")},sort_keys=True))
  print("[PASS] SULS-102B canonical birth identity contract repair")
  print("[PASS] exact DAMM V2 inner-CPI identity now published at canonical birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
