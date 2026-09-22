from __future__ import annotations
import json
from pathlib import Path

def _key(keys,x):
 if isinstance(x,str): return x
 if isinstance(x,int) and 0<=x<len(keys):
  v=keys[x];return v.get("pubkey") if isinstance(v,dict) else v
 return None

def normalize_birth(b):
 env=b.get("envelope") or {};raw=env.get("raw_transaction") or {}
 tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
 keys=msg.get("accountKeys") or []
 programs=[];instructions=[]
 def add_ix(ix,outer_index=None,inner=False):
  if not isinstance(ix,dict): return
  program=ix.get("programId") or _key(keys,ix.get("programIdIndex"))
  accounts=[_key(keys,x) for x in (ix.get("accounts") or [])]
  if program and program not in programs: programs.append(program)
  parsed=ix.get("parsed") or {}
  instructions.append({"program_id":program,"accounts":accounts,"inner":inner,
   "outer_index":outer_index,"parsed_type":parsed.get("type"),"data":ix.get("data")})
 for i,ix in enumerate(msg.get("instructions") or []):add_ix(ix,i,False)
 for grp in meta.get("innerInstructions") or []:
  for ix in grp.get("instructions") or []:add_ix(ix,grp.get("index"),True)
 balances=[]
 for side in ("preTokenBalances","postTokenBalances"):
  for x in meta.get(side) or []:
   balances.append({"side":side,"account_index":x.get("accountIndex"),
    "mint":x.get("mint"),"owner":x.get("owner"),"program_id":x.get("programId"),
    "ui_amount_string":((x.get("uiTokenAmount") or {}).get("uiAmountString"))})
 return {"signature":b.get("signature"),"slot":b.get("slot"),"block_time":b.get("block_time"),
  "observed_unix":b.get("observed_unix"),"age_seconds":b.get("age_seconds"),
  "program_ids":programs,"account_keys":[_key(keys,i) for i in range(len(keys))],
  "instructions":instructions,"token_balances":balances,
  "logs":meta.get("logMessages") or [],
  "raw_envelope_present":bool(raw),"execution_authority":False}

def normalize_cohort(root):
 p=Path(root)/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 rows=[normalize_birth(x) for x in (d.get("births") or [])]
 return {"revision":"USLS_002","row_count":len(rows),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=normalize_cohort(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/universal_transaction_shapes.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
