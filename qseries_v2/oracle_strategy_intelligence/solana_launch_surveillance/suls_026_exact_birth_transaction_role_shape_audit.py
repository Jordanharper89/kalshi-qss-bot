from __future__ import annotations
import json
from pathlib import Path

def audit(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for t in d.get("transactions",[]):
  e=t.get("envelope") or {}
  raw=e.get("raw_transaction") or {}
  tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
  rows.append({
   "slot":e.get("slot"),"signature":e.get("signature"),
   "account_keys":e.get("account_keys") or msg.get("accountKeys") or [],
   "outer_instructions":e.get("instructions") or msg.get("instructions") or [],
   "inner_instructions":e.get("inner_instructions") or meta.get("innerInstructions") or [],
   "pre_token_balances":e.get("pre_token_balances") or meta.get("preTokenBalances") or [],
   "post_token_balances":e.get("post_token_balances") or meta.get("postTokenBalances") or [],
  })
 return {"revision":"SULS_026","rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_birth_role_shape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
