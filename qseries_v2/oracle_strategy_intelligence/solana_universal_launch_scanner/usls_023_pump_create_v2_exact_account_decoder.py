from __future__ import annotations
import json
from pathlib import Path
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
SYSTEM="11111111111111111111111111111111"
TOKEN2022="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ATA="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
WSOL="So11111111111111111111111111111111111111112"
ROLES=("mint","mint_authority","bonding_curve","associated_bonding_curve","global","user",
"system_program","token_program","associated_token_program","mayhem_program_id","global_params",
"sol_vault","mayhem_state","mayhem_token_vault","event_authority","program")

def decode(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"pump_create_v2_live_capture.json").read_text(encoding="utf-8"))
 rows=[]
 for b in src.get("births") or []:
  for ix in b.get("instructions") or []:
   a=ix.get("accounts") or []
   if len(a)<16:continue
   m={ROLES[i]:a[i] for i in range(16)}
   optional=a[16:]
   m["quote_mint"]=optional[0] if len(optional)>=3 else WSOL
   m["associated_quote_bonding_curve"]=optional[1] if len(optional)>=3 else None
   m["quote_token_program"]=optional[2] if len(optional)>=3 else None
   checks={"system_program":m["system_program"]==SYSTEM,"token_program":m["token_program"]==TOKEN2022,
    "associated_token_program":m["associated_token_program"]==ATA,"program":m["program"]==PUMP,
    "distinct_mint_curve":m["mint"]!=m["bonding_curve"]}
   rows.append({"signature":b["signature"],"slot":b.get("slot"),"observed_unix":b.get("observed_unix"),
    "block_time":b.get("block_time"),**m,"checks":checks,"all_checks":all(checks.values()),
    "execution_authority":False})
 return {"revision":"USLS_023","decoded_count":len(rows),
  "certified_count":sum(1 for x in rows if x["all_checks"]),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=decode(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_decoded_births.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
