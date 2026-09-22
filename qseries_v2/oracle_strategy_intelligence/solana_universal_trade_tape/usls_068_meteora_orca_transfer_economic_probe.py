from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

def parent(level):
 try:return int(str(level).split(":",1)[1])
 except Exception:return None

def signers(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") for x in ks if isinstance(x,dict) and x.get("signer") and x.get("pubkey")]

def owner_deltas(tx,owner):
 meta=(tx or {}).get("meta") or {};z=defaultdict(lambda:[0,0,None])
 for j,key in ((0,"preTokenBalances"),(1,"postTokenBalances")):
  for x in meta.get(key) or []:
   if x.get("owner")!=owner or not x.get("mint"):continue
   u=x.get("uiTokenAmount") or {};z[x["mint"]][j]+=int(u.get("amount") or 0);z[x["mint"]][2]=u.get("decimals")
 return {m:(b-a)/(10**int(d)) for m,(a,b,d) in z.items() if d is not None and b!=a}

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  cand=[]
  for s in signers(x["transaction"]):
   d=owner_deltas(x["transaction"],s);neg=[(m,-v) for m,v in d.items() if v<0];pos=[(m,v) for m,v in d.items() if v>0]
   if len(neg)==1 and len(pos)==1:cand.append((s,neg[0],pos[0]))
  trader,inp,out=(cand[0] if len(cand)==1 else (None,(None,None),(None,None)))
  im,ia=inp;om,oa=out;exact=trader is not None and ia and oa
  rows.append({"venue":x["venue"],"signature":x["signature"],"instruction_name":x["instruction_name"],
   "level":x["level"],"instruction_ordinal":x["instruction_ordinal"],"trader":trader,
   "input_mint":im,"input_amount":ia,"output_mint":om,"output_amount":oa,
   "decoder_state":"EXACT_TWO_ASSET_SIGNER_ECONOMICS_POOL_ROLE_PENDING" if exact else "SIGNER_ECONOMICS_AMBIGUOUS",
   "accounts":x["accounts"],"execution_authority":False})
 return {"revision":"USLS_068","row_count":len(rows),
  "exact_two_asset_count":sum(x["decoder_state"].startswith("EXACT_TWO_ASSET") for x in rows),
  "venue_exact_counts":{v:sum(x["venue"]==v and x["decoder_state"].startswith("EXACT_TWO_ASSET") for x in rows)
   for v in sorted({x["venue"] for x in rows})},
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_transfer_economic_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
