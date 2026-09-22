from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_073_meteora_dbc_physical_role_discovery.py"
TEST=ROOT/"test_usls_073_meteora_dbc_physical_role_discovery.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_instruction_transfer_evidence.json").read_text(encoding="utf-8"))
 rows=[];account_positions=Counter()
 for x in src["rows"]:
  if x["venue"]!="METEORA_DBC":continue
  ac=x["accounts"];aset=set(ac)
  touched=set()
  for t in x["transfers"]:
   if t.get("source") in aset:touched.add(t["source"])
   if t.get("destination") in aset:touched.add(t["destination"])
  positions=[i for i,a in enumerate(ac) if a in touched]
  for i in positions:account_positions[i]+=1
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],
   "account_count":len(ac),"transfer_count":x["transfer_count"],"transfer_touched_account_positions":positions,
   "transfer_touched_accounts":[ac[i] for i in positions],"execution_authority":False})
 return {"revision":"USLS_073","dbc_row_count":len(rows),
  "recurrent_transfer_touched_positions":[{"index":i,"count":c} for i,c in account_positions.most_common()],
  "rows":rows,"role_certified":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_dbc_physical_role_discovery.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_073_meteora_dbc_physical_role_discovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_discovery(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"dbc_row_count":d["dbc_row_count"],
   "recurrent_transfer_touched_positions":d["recurrent_transfer_touched_positions"][:12],"role_certified":d["role_certified"]},sort_keys=True))
  self.assertGreater(d["dbc_row_count"],0);self.assertGreater(len(d["recurrent_transfer_touched_positions"]),0)
  self.assertFalse(d["role_certified"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-073 DBC physical role discovery evidence")
  print("[PASS] recurrent transfer-linked account positions measured; no guessed certification")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")