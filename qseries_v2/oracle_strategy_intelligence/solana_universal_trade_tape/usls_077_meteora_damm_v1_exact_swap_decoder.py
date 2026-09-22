from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import CORRECT_PROGRAM,SWAP_DISC
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def all_ix(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for i,ix in enumerate(msg.get("instructions") or []):out.append(("top",i,ix))
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for i,ix in enumerate(g.get("instructions") or []):out.append((f"inner:{g.get('index')}",i,ix))
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_damm_v1_deep_transactions.json").read_text(encoding="utf-8"));rows=[]
 for r in src["rows"]:
  if not r["hydrated"]:continue
  tx=r["transaction"];ks=keys(tx)
  for level,ordinal,ix in all_ix(tx):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=CORRECT_PROGRAM or not ix.get("data") or b58d(ix["data"])[:8]!=SWAP_DISC:continue
   ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
   rows.append({"signature":r["signature"],"level":level,"instruction_ordinal":ordinal,"accounts":ac,
    "pool":ac[0] if len(ac)>0 else None,"user_source":ac[1] if len(ac)>1 else None,
    "user_destination":ac[2] if len(ac)>2 else None,"a_token_vault":ac[5] if len(ac)>5 else None,
    "b_token_vault":ac[6] if len(ac)>6 else None,"trader":ac[12] if len(ac)>12 else None,
    "transaction":tx,"execution_authority":False})
 return {"revision":"USLS_077","exact_swap_count":len(rows),"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_exact_swaps.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
