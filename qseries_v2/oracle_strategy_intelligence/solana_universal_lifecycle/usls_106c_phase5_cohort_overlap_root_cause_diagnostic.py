from __future__ import annotations
import json
from pathlib import Path

SOURCES=[
 ("BIRTH","runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json","events"),
 ("BIRTH","runtime_state/solana_opportunities/universal_launch_scanner/canonical_universal_birth_events.json","events"),
 ("TRADE","runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json","rows"),
 ("TRADE","runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_universal_trade_rows.json","rows"),
 ("TRADE","runtime_state/solana_opportunities/universal_trade_tape/launchlab_universal_trade_rows.json","rows"),
]

def pick(x,names):
 for n in names:
  v=x.get(n)
  if v not in (None,""):return v
 return None

def norm(x):
 return {
  "venue":pick(x,("venue","launcher_family","family","source_family")),
  "program_id":pick(x,("program_id","program")),
  "token":pick(x,("token_address","token_mint","mint","base_mint","token")),
  "market":pick(x,("market_address","pair_address","pool","bonding_curve","curve")),
  "signature":pick(x,("birth_signature","trade_signature","signature")),
  "slot":pick(x,("birth_slot","trade_slot","slot")),
  "time":pick(x,("birth_observed_unix","trade_observed_unix","observed_unix","block_time"))
 }

def rng(vals):
 vals=[float(v) for v in vals if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace(".","",1).isdigit())]
 return {"min":min(vals) if vals else None,"max":max(vals) if vals else None}

def summarize(root,kind,path,key):
 p=Path(root)/path
 if not p.exists():return {"kind":kind,"path":path,"missing":True}
 d=json.loads(p.read_text(encoding="utf-8"));rs=[norm(x) for x in (d.get(key) or []) if isinstance(x,dict)]
 return {"kind":kind,"path":path,"revision":d.get("revision"),"row_count":len(rs),
  "non_null":{"venue":sum(bool(x["venue"]) for x in rs),"program_id":sum(bool(x["program_id"]) for x in rs),
   "token":sum(bool(x["token"]) for x in rs),"market":sum(bool(x["market"]) for x in rs),
   "signature":sum(bool(x["signature"]) for x in rs),"slot":sum(x["slot"] is not None for x in rs),"time":sum(x["time"] is not None for x in rs)},
  "slot_range":rng([x["slot"] for x in rs]),"time_range":rng([x["time"] for x in rs]),
  "sample":[x for x in rs[:5]]}

def overlap(a,b,key):
 av={x[key] for x in a if x.get(key)};bv={x[key] for x in b if x.get(key)}
 return len(av&bv)

def load_norm(root,path,key):
 d=json.loads((Path(root)/path).read_text(encoding="utf-8"))
 return [norm(x) for x in (d.get(key) or []) if isinstance(x,dict)]

def build(root):
 sums=[summarize(root,*s) for s in SOURCES]
 pairs=[]
 births=[s for s in SOURCES if s[0]=="BIRTH"];trades=[s for s in SOURCES if s[0]=="TRADE"]
 for b in births:
  br=load_norm(root,b[1],b[2])
  for t in trades:
   tr=load_norm(root,t[1],t[2])
   pairs.append({"birth_path":b[1],"trade_path":t[1],
    "token_overlap":overlap(br,tr,"token"),"market_overlap":overlap(br,tr,"market"),
    "signature_overlap":overlap(br,tr,"signature"),"program_overlap":overlap(br,tr,"program_id")})
 return {"revision":"USLS_106C","sources":sums,"pairs":pairs,
  "diagnostic_only":True,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_cohort_overlap_root_cause.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
