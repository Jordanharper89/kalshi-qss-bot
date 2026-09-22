from __future__ import annotations
import json,time
from pathlib import Path

TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"
OUT="runtime_state/solana_opportunities/solana_scanner/phase5_exact_lifecycle_join_repair.json"

def _rows(p):
 out=[]
 if not p.exists():return out
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try:out.append(json.loads(line))
   except Exception:pass
 return out

def _payload(r):
 p=r.get("payload")
 return p if isinstance(p,dict) else r

def _walk_values(x,key):
 out=[]
 if isinstance(x,dict):
  if key in x:out.append(x.get(key))
  for v in x.values():out.extend(_walk_values(v,key))
 elif isinstance(x,list):
  for v in x:out.extend(_walk_values(v,key))
 return [v for v in out if v not in (None,"")]

def _all_strings(x):
 out=[]
 if isinstance(x,str):out.append(x)
 elif isinstance(x,dict):
  for v in x.values():out.extend(_all_strings(v))
 elif isinstance(x,list):
  for v in x:out.extend(_all_strings(v))
 return out

def _first(x,*keys):
 for k in keys:
  vals=_walk_values(x,k)
  if vals:return vals[0]
 return None

def _trade_identity(t):
 p=_payload(t)
 fam=_first(p,"family","venue","program_family","source_family")
 sig=_first(p,"signature","trade_signature")
 slot=_first(p,"slot","trade_slot")
 obs=_first(p,"observed_unix","trade_observed_unix","received_unix","scanner_observed_unix")
 prog=_first(p,"program_id","programId")
 token=_first(p,"token_address","token","mint","base_mint","trade_mint")
 market=_first(p,"market_address","pool","pool_address","bonding_curve","curve","amm")
 side=_first(p,"side","trade_side")
 exact=_first(p,"exact_trade","is_exact_trade","decoder_state","trade_type")
 return {"family":fam,"signature":sig,"slot":slot,"observed_unix":obs,
  "program_id":prog,"token_address":token,"market_address":market,
  "side":side,"exact_marker":exact,"strings":set(_all_strings(p))}

def _birth_identity(b):
 p=_payload(b)
 return {"signature":_first(p,"signature","birth_signature"),
  "slot":_first(p,"slot","birth_slot"),
  "observed_unix":_first(p,"observed_unix","birth_observed_unix"),
  "family":_first(p,"family","venue"),
  "program_id":_first(p,"program_id"),
  "token_address":_first(p,"token_address","mint"),
  "market_address":_first(p,"market_address","bonding_curve","curve")}

def _chrono(b,t):
 try:
  if b["slot"] is not None and t["slot"] is not None:
   return int(t["slot"])>=int(b["slot"])
 except Exception:pass
 try:
  if b["observed_unix"] is not None and t["observed_unix"] is not None:
   return float(t["observed_unix"])>=float(b["observed_unix"])
 except Exception:pass
 return False

def _match(b,t):
 # Exact identity evidence only. Never join on family/time alone.
 market=b.get("market_address");token=b.get("token_address")
 prog=b.get("program_id")
 market_hit=bool(market and (market==t.get("market_address") or market in t["strings"]))
 token_hit=bool(token and (token==t.get("token_address") or token in t["strings"]))
 program_ok=(not prog or not t.get("program_id") or prog==t.get("program_id") or prog in t["strings"])
 return program_ok and market_hit and token_hit and _chrono(b,t)

def run(root):
 root=Path(root);rows=_rows(root/TAPE)
 births=[r for r in rows if r.get("record_type")=="BIRTH"]
 trades=[r for r in rows if r.get("record_type")=="TRADE"]
 binfo=[_birth_identity(x) for x in births]
 tinfo=[_trade_identity(x) for x in trades]
 joins=[];unjoined=[]
 for b in binfo:
  cand=[t for t in tinfo if _match(b,t)]
  cand.sort(key=lambda t:(int(t["slot"]) if str(t.get("slot","")).isdigit() else 10**20,
                          float(t["observed_unix"]) if t.get("observed_unix") is not None else 10**20))
  if cand:
   t=cand[0]
   joins.append({"birth":b,"first_trade":{k:v for k,v in t.items() if k!="strings"},
    "join_evidence":{"token_exact":True,"market_exact":True,
     "program_compatible":True,"chronology":True},
    "execution_authority":False})
  else:unjoined.append(b)

 # Truth diagnostics for why prior materializer could not join.
 trade_with_token=sum(t["token_address"] is not None for t in tinfo)
 trade_with_market=sum(t["market_address"] is not None for t in tinfo)
 birth_addresses=set()
 for b in binfo:
  if b.get("token_address"):birth_addresses.add(b["token_address"])
  if b.get("market_address"):birth_addresses.add(b["market_address"])
 rows_with_any_birth_address=sum(bool(birth_addresses & t["strings"]) for t in tinfo)

 return {"revision":"USLS_107C","source_revision":"USLS_107B",
  "tape_row_count":len(rows),"birth_count":len(births),"trade_count":len(trades),
  "birth_identity_complete_count":sum(bool(b.get("token_address") and b.get("market_address")) for b in binfo),
  "trade_rows_with_explicit_token":trade_with_token,
  "trade_rows_with_explicit_market":trade_with_market,
  "trade_rows_containing_any_fresh_birth_address":rows_with_any_birth_address,
  "exact_identity_lifecycle_join_count":len(joins),
  "joins":joins,"unjoined_births":unjoined,
  "finding":("EXACT_BIRTH_TRADE_IDENTITY_JOIN_PROVEN" if joins else
   "UNIVERSAL_RAW_TRADE_LANE_LACKS_JOINABLE_EXACT_IDENTITY"),
  "required_next_boundary":("PHASE5_CERTIFICATION" if joins else
   "EXACT_PUMP_TRADE_NORMALIZATION_INTO_SCANNER_TAPE"),
  "no_family_time_only_join":True,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
