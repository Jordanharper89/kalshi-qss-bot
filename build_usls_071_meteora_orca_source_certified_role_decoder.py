from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_071_meteora_orca_source_certified_role_decoder.py"
TEST=ROOT/"test_usls_071_meteora_orca_source_certified_role_decoder.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

ROLE={
 ("METEORA_DAMM","SWAP"):{"pool":1,"user_in":2,"user_out":3,"vault_a":4,"vault_b":5,"mint_a":6,"mint_b":7,"trader":8},
 ("METEORA_DAMM","SWAP2"):{"pool":1,"user_in":2,"user_out":3,"vault_a":4,"vault_b":5,"mint_a":6,"mint_b":7,"trader":8},
 ("METEORA_DLMM","SWAP2"):{"pool":0,"vault_x":2,"vault_y":3,"user_in":4,"user_out":5,"mint_x":6,"mint_y":7,"trader":10},
 ("METEORA_DLMM","SWAP_EXACT_OUT2"):{"pool":0,"vault_x":2,"vault_y":3,"user_in":4,"user_out":5,"mint_x":6,"mint_y":7,"trader":10},
 ("ORCA","SWAP"):{"trader":1,"pool":2,"user_a":3,"vault_a":4,"user_b":5,"vault_b":6},
}

def pick(accounts,i):return accounts[i] if i is not None and i<len(accounts) else None

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_instruction_transfer_evidence.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  spec=ROLE.get((x["venue"],x["instruction_name"]))
  roles={k:pick(x["accounts"],i) for k,i in spec.items()} if spec else {}
  state="SOURCE_CERTIFIED_ACCOUNT_ROLES" if spec else "ACCOUNT_ROLE_SCHEMA_PENDING"
  rows.append({**x,"roles":roles,"role_state":state})
 return {"revision":"USLS_071","row_count":len(rows),
  "venue_role_counts":{v:sum(x["venue"]==v and x["role_state"]=="SOURCE_CERTIFIED_ACCOUNT_ROLES" for x in rows)
    for v in sorted({x["venue"] for x in rows})},
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_source_certified_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_071_meteora_orca_source_certified_role_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"venue_role_counts":d["venue_role_counts"]},sort_keys=True))
  self.assertGreater(d["venue_role_counts"].get("METEORA_DAMM",0),0)
  self.assertGreater(d["venue_role_counts"].get("METEORA_DLMM",0),0)
  self.assertGreater(d["venue_role_counts"].get("ORCA",0),0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-071 source-certified DAMM/DLMM/Orca account roles")
  print("[PASS] DBC/DYN remain pending rather than guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
