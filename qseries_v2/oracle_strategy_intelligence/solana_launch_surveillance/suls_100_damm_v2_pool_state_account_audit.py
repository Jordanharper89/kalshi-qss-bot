from __future__ import annotations
import json

def audit(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 births=list(json.loads(p.read_text(encoding="utf-8")).get("births") or [])
 if not births:raise RuntimeError("NO_BIRTHS")
 b=births[-1];raw=(b.get("envelope") or {}).get("raw_transaction") or {}
 tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
 keys=msg.get("accountKeys") or []
 def key(i):
  if not isinstance(i,int) or i>=len(keys):return None
  x=keys[i];return x.get("pubkey") if isinstance(x,dict) else x
 ins=[]
 for n,ix in enumerate(msg.get("instructions") or []):
  ac=ix.get("accounts") or []
  ins.append({"index":n,"programId":ix.get("programId"),
   "programIdIndex":ix.get("programIdIndex"),
   "resolved_program":key(ix.get("programIdIndex")),
   "accounts":[key(i) if isinstance(i,int) else i for i in ac],
   "data":ix.get("data")})
 return {"revision":"SULS_100","signature":b.get("signature"),
  "account_keys":keys,"instructions":ins,
  "preTokenBalances":meta.get("preTokenBalances") or [],
  "postTokenBalances":meta.get("postTokenBalances") or [],
  "logs":meta.get("logMessages") or [],
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/damm_v2_pool_state_account_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
