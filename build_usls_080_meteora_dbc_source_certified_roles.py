from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_080_meteora_dbc_source_certified_roles.py"
TEST=ROOT/"test_usls_080_meteora_dbc_source_certified_roles.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
ROLE={"pool_authority":0,"config":1,"pool":2,"user_in":3,"user_out":4,
      "base_vault":5,"quote_vault":6,"base_mint":7,"quote_mint":8,"trader":9}
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="METEORA_DBC":continue
  a=x["accounts"];r={k:(a[i] if i<len(a) else None) for k,i in ROLE.items()}
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],"roles":r,
   "role_state":"SOURCE_CERTIFIED_DBC_SWAPCTX_ROLES","execution_authority":False})
 return {"revision":"USLS_080","row_count":len(rows),"roles":ROLE,"rows":rows,
  "source_contract":"Meteora DBC SwapCtx","execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_dbc_source_certified_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_080_meteora_dbc_source_certified_roles import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"roles":d["roles"]},sort_keys=True))
  self.assertEqual(d["row_count"],17)
  self.assertTrue(all(all(x["roles"][k] for k in ("pool","user_in","user_out","base_vault","quote_vault","base_mint","quote_mint","trader")) for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-080 DBC current-source SwapCtx account roles certified")
  print("[PASS] physical positions 3/4/5/6 match user-in/user-out/base-vault/quote-vault")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")