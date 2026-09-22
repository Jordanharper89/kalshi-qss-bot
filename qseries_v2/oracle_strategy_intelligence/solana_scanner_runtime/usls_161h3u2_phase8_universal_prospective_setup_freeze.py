from __future__ import annotations
import hashlib,json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase8_universal_live_certified_producer_bridge.json"

def _canon(x):
 return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 rows=[x for x in d.get("rows",[])
       if x.get("market_address") is not None
       and isinstance(x.get("effective_price"),(int,float))
       and isinstance(x.get("observed_unix"),(int,float))]
 groups={}
 for x in rows:
  groups.setdefault((x["family"],str(x["market_address"])),[]).append(x)
 freezes=[]
 for (fam,market),xs in groups.items():
  xs.sort(key=lambda x:x["observed_unix"])
  prices=[float(x["effective_price"]) for x in xs]
  if not prices:continue
  first,last=prices[0],prices[-1]
  t0,tn=xs[0]["observed_unix"],xs[-1]["observed_unix"]
  duration=max(1e-9,float(tn)-float(t0))
  f={"family":fam,"market_address":market,"freeze_unix":time.time(),
   "source_first_observed_unix":t0,"source_last_observed_unix":tn,
   "trade_count":len(xs),"trade_velocity":len(xs)/duration,
   "first_price":first,"last_price":last,
   "return_to_freeze":last/first-1 if first else None,
   "mfe_to_freeze":max(prices)/first-1 if first else None,
   "mae_to_freeze":min(prices)/first-1 if first else None,
   "source_signatures":[x.get("trade_signature") for x in xs],
   "future_outcome":None,"future_data_allowed_at_freeze":False,
   "execution_authority":False}
  f["freeze_hash"]=hashlib.sha256(_canon(f).encode()).hexdigest()
  freezes.append(f)
 fams=sorted({x["family"] for x in freezes})
 return {"revision":"USLS_161H3U2","frozen_setup_count":len(freezes),
  "family_count":len(fams),"families":fams,"frozen_setups":freezes,
  "freeze_rule":"ONLY_ROWS_OBSERVED_BEFORE_FREEZE_HASH_NO_FUTURE_DATA",
  "source_revision":d.get("revision"),
  "next_boundary":"UNIVERSAL_PROSPECTIVE_FORWARD_OUTCOME_COLLECTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_prospective_freezes_v2.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
