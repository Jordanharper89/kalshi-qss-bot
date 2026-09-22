from __future__ import annotations
import hashlib,json
from pathlib import Path

TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"
OUT="runtime_state/solana_opportunities/solana_scanner/lifecycle_state.json"

def pick(x,*names):
 for n in names:
  v=x.get(n)
  if v not in (None,""): return v
 return None

def norm_payload(p):
 if not isinstance(p,dict): return {}
 return {
  "venue":pick(p,"venue","launcher_family","family","source_family"),
  "program_id":pick(p,"program_id","program"),
  "token_address":pick(p,"token_address","token_mint","mint","base_mint","token"),
  "market_address":pick(p,"market_address","pair_address","pool","bonding_curve","curve"),
  "signature":pick(p,"signature","birth_signature","trade_signature"),
  "slot":pick(p,"slot","birth_slot","trade_slot"),
  "observed_unix":pick(p,"observed_unix","birth_observed_unix","trade_observed_unix","block_time"),
  "side":pick(p,"side"),
  "trader":pick(p,"trader","user","payer"),
  "input_asset":pick(p,"input_asset","quote_mint"),
  "input_amount":pick(p,"input_amount","quote_amount"),
  "output_asset":pick(p,"output_asset","token_address","token_mint"),
  "output_amount":pick(p,"output_amount","base_amount"),
  "decoder_state":pick(p,"decoder_state","state")
 }

def key(x):
 parts=(x.get("program_id"),x.get("token_address"),x.get("market_address"))
 if all(parts): return ("PROGRAM_TOKEN_MARKET",)+parts
 parts=(x.get("venue"),x.get("token_address"),x.get("market_address"))
 if all(parts): return ("VENUE_TOKEN_MARKET",)+parts
 return None

def lifecycle_id(k):
 return hashlib.sha256("|".join(map(str,k)).encode()).hexdigest() if k else None

def read_tape(root):
 p=Path(root)/TAPE;rows=[]
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip(): rows.append(json.loads(line))
 return rows

def build(root):
 raw=read_tape(root)
 births=[];trades=[]
 for r in raw:
  item={"record_id":r.get("record_id"),"scanner_observed_unix":r.get("scanner_observed_unix"),
        "normalized":norm_payload(r.get("payload")),"raw_payload":r.get("payload"),
        "execution_authority":False}
  (births if r.get("record_type")=="BIRTH" else trades if r.get("record_type")=="TRADE" else []).append(item)

 birth_index={}
 for b in births:
  k=key(b["normalized"])
  if k: birth_index.setdefault(k,[]).append(b)

 lifecycles=[];unresolved=[];joined=0
 for t in trades:
  k=key(t["normalized"])
  matches=birth_index.get(k,[]) if k else []
  if matches:
   b=sorted(matches,key=lambda x:(x["normalized"].get("slot") or 0,x["scanner_observed_unix"] or 0))[0]
   lifecycles.append({"lifecycle_id":lifecycle_id(k),"identity_key":list(k),
    "birth_record_id":b["record_id"],"trade_record_id":t["record_id"],
    "birth":b["normalized"],"trade":t["normalized"],"execution_authority":False})
   joined+=1
  else:
   unresolved.append({"trade_record_id":t["record_id"],"identity_key":list(k) if k else None,
    "trade":t["normalized"],"raw_payload":t["raw_payload"],
    "state":"RETAIN_UNRESOLVED_BIRTH","execution_authority":False})

 used_birth={x["birth_record_id"] for x in lifecycles}
 pending_births=[{"birth_record_id":b["record_id"],"birth":b["normalized"],
  "state":"RETAIN_PENDING_FIRST_TRADE","execution_authority":False} for b in births if b["record_id"] not in used_birth]

 return {"revision":"USLS_106M","source_revision":"USLS_106L",
  "raw_record_count":len(raw),"birth_record_count":len(births),"trade_record_count":len(trades),
  "joined_trade_count":joined,"unresolved_trade_count":len(unresolved),
  "pending_birth_count":len(pending_births),"accounting_ok":joined+len(unresolved)==len(trades),
  "lifecycles":lifecycles,"unresolved_trades":unresolved,"pending_births":pending_births,
  "unknown_retention":"RETAIN_UNRESOLVED","birth_without_trade":"RETAIN_PENDING_FIRST_TRADE",
  "lifecycle_join_certified":False,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
