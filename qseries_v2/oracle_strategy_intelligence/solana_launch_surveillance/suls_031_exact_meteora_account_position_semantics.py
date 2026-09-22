from __future__ import annotations
import json
from pathlib import Path
WSOL="So11111111111111111111111111111111111111112"

def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for t in d.get("transactions",[]):
  e=t.get("envelope") or {};raw=e.get("raw_transaction") or {};meta=raw.get("meta") or {}
  created=[];transfers=[];position_mints=set()
  for grp in meta.get("innerInstructions") or []:
   for ix in grp.get("instructions") or []:
    if not isinstance(ix,dict):continue
    parsed=ix.get("parsed") or {};info=parsed.get("info") or {};typ=parsed.get("type")
    if typ=="createAccount":
     created.append({"account":info.get("newAccount"),"owner_program":info.get("owner"),
      "space":info.get("space"),"lamports":info.get("lamports")})
    if typ in ("transferChecked","transfer"):
     transfers.append({"type":typ,"source":info.get("source"),"destination":info.get("destination"),
      "mint":info.get("mint"),"amount":(info.get("tokenAmount") or {}).get("uiAmountString")})
    if typ=="initializeTokenMetadata" and info.get("name")=="Meteora Position NFT":
     position_mints.add(info.get("mint"))
  rows.append({"signature":e.get("signature"),"created_accounts":created,"transfers":transfers,
   "position_nft_mints":sorted(x for x in position_mints if x),"wsol_mint":WSOL})
 return {"revision":"SULS_031","rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/meteora_account_position_semantics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
