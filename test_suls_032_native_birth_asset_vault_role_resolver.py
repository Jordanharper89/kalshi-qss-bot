import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_032_native_birth_asset_vault_role_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT)
  for r in d["rows"]:print("[ASSET_ROLES]",json.dumps(r,sort_keys=True))
  if not any(r["roles_resolved"] for r in d["rows"]):self.fail("BIRTH_ASSET_VAULT_ROLES_NOT_RESOLVED")
  print("[PASS] SULS-032 native birth asset/vault role resolver")
if __name__=="__main__":unittest.main()
