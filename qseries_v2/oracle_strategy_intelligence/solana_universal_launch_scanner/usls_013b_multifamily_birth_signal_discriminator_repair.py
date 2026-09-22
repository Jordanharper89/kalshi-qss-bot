from __future__ import annotations
import json
from pathlib import Path

BIRTH_TERMS=("initialize","create","launch","migration","pool","mintto","initializepool","create_pool","new_pool")
TRADE_TERMS=("swap","buy","sell","exactin","exactout")

def discriminate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"))
 rows=[]
 for x in d.get("rows") or []:
  tx=x.get("raw_transaction") or {}
  meta=tx.get("meta") or {}
  logs=[str(v) for v in (meta.get("logMessages") or [])]
  low=" ".join(logs).lower()
  birth_hits=sorted({t for t in BIRTH_TERMS if t in low})
  trade_hits=sorted({t for t in TRADE_TERMS if t in low})
  pre=meta.get("preTokenBalances") or []
  post=meta.get("postTokenBalances") or []
  new_indexes=sorted(set(v.get("accountIndex") for v in post)-set(v.get("accountIndex") for v in pre))
  score=min(5,len(birth_hits)+int(bool(new_indexes))+int("success" in low))
  state=("PROBABLE_BIRTH" if score>=3 else
         "POSSIBLE_BIRTH" if score>=2 else
         "ACTIVITY_NOT_BIRTH_PROVEN")
  families=list(x.get("families") or ([] if not x.get("family") else [x.get("family")]))
  rows.append({"families":families,"signature":x.get("signature"),"slot":x.get("slot"),
   "state":state,"birth_hits":birth_hits,"trade_hits":trade_hits,
   "new_token_balance_indexes":new_indexes,"birth_score":score,
   "hydrated":bool(x.get("hydrated")),"execution_authority":False})
 fams=sorted({f for r in rows for f in r["families"]})
 return {"revision":"USLS_013B","sample_count":len(rows),
  "family_count":len(fams),"families":fams,
  "probable_birth_count":sum(1 for x in rows if x["state"]=="PROBABLE_BIRTH"),
  "possible_birth_count":sum(1 for x in rows if x["state"]=="POSSIBLE_BIRTH"),
  "routine_activity_count":sum(1 for x in rows if x["state"]=="ACTIVITY_NOT_BIRTH_PROVEN"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=discriminate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_birth_signal_discrimination.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
