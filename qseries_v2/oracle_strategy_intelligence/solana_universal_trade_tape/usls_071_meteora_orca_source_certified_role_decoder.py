from __future__ import annotations
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
