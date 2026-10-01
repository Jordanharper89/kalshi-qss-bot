from __future__ import annotations
import json
from collections import Counter,defaultdict
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_031_pump_exact_trade_discriminator_registry import PUMP,classify
SRC="runtime_state/solana_opportunities/universal_trade_tape/pump_trade_raw_transactions.json"
def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 out=[x.get("pubkey") if isinstance(x,dict) else x for x in ks]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return out+(la.get("writable") or [])+(la.get("readonly") or [])
def instructions(tx):
 ks=keys(tx);msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 groups=[("top",i,x) for i,x in enumerate(msg.get("instructions") or [])]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  groups += [(f"inner:{g.get('index')}",i,x) for i,x in enumerate(g.get("instructions") or [])]
 for level,i,ix in groups:
  pid=ix.get("programId")
  if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
  if pid!=PUMP:continue
  c=classify(ix.get("data") or "")
  ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
  out.append((level,i,c,ac))
 return out
def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"));pos=defaultdict(Counter);matched=0
 for r in d.get("rows",[]):
  tx=r.get("raw_transaction") or {};market=str(r.get("market_address") or "")
  if not market:continue
  for level,i,c,ac in instructions(tx):
   name=c.get("instruction_name")
   if not name:continue
   hits=[j for j,a in enumerate(ac) if str(a)==market]
   if len(hits)==1:pos[name][hits[0]]+=1;matched+=1
 roles={}
 for name,c in pos.items():
  total=sum(c.values());idx,n=c.most_common(1)[0];conf=n/total if total else 0
  roles[name]={"market_account_index":idx,"support":total,"winner_count":n,"confidence":conf,
   "certified":total>=3 and conf==1.0}
 return {"revision":"USLS_162F","matched_trade_instructions":matched,"roles":roles,
  "all_observed_trade_types_certified":bool(roles) and all(x["certified"] for x in roles.values()),
  "policy":"KNOWN_CURVE_MATCH_INSIDE_EXACT_PUMP_TRADE_INSTRUCTION_ONLY",
  "next_boundary":"PUMP_FUN_DIRECT_TRANSACTION_DECODER_FROM_CERTIFIED_ROLE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/pump_trade_market_role_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
