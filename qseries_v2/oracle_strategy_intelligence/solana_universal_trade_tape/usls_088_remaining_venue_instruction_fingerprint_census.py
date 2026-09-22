from __future__ import annotations
import json
from collections import Counter,defaultdict
from pathlib import Path
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
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_live_transactions.json").read_text(encoding="utf-8"));freq=defaultdict(Counter);examples={}
 for r in src["rows"]:
  if not r["hydrated"]:continue
  ks=keys(r["transaction"])
  for level,ordinal,ix in all_ix(r["transaction"]):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=r["program_id"] or not ix.get("data"):continue
   raw=b58d(ix["data"]);disc=raw[:8].hex() if len(raw)>=8 else raw.hex()
   freq[r["venue"]][disc]+=1;examples.setdefault((r["venue"],disc),{"signature":r["signature"],"level":level,"ordinal":ordinal,"account_count":len(ix.get("accounts") or [])})
 rows=[]
 for v,c in freq.items():
  for disc,n in c.most_common():
   rows.append({"venue":v,"discriminator_hex":disc,"count":n,"example":examples[(v,disc)],"semantic_state":"UNKNOWN_INSTRUCTION_TYPE"})
 return {"revision":"USLS_088","fingerprint_count":len(rows),"rows":rows,"unknown_instruction_retention":True,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_instruction_fingerprints.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
