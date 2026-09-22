from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_092_remaining_venue_exact_account_roles.py"
TEST=ROOT/"test_usls_092_remaining_venue_exact_account_roles.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_trade_census.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  roles={k:(x["accounts"][i] if i<len(x["accounts"]) else None) for i,k in enumerate(x["role_names"])}
  ok=all(roles.values())
  rows.append({"venue":x["venue"],"signature":x["signature"],"level":x["level"],"instruction_ordinal":x["instruction_ordinal"],
   "instruction_name":x["instruction_name"],"side":x["side"],"roles":roles,
   "role_state":"SOURCE_LAYOUT_EXACT" if ok else "ACCOUNT_ROLE_INCOMPLETE","transaction":x["transaction"],"execution_authority":False})
 return {"revision":"USLS_092","row_count":len(rows),"exact_role_count":sum(x["role_state"]=="SOURCE_LAYOUT_EXACT" for x in rows),
  "venue_exact_role_counts":{v:sum(x["venue"]==v and x["role_state"]=="SOURCE_LAYOUT_EXACT" for x in rows) for v in ("MOONIT","BOOP_FUN","HEAVEN")},
  "rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_exact_account_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_092_remaining_venue_exact_account_roles import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_role_count":d["exact_role_count"],"venue_exact_role_counts":d["venue_exact_role_counts"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_role_count"],d["row_count"],"SOURCE_ACCOUNT_LAYOUT_INCOMPLETE")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-092 exact source-backed account roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")