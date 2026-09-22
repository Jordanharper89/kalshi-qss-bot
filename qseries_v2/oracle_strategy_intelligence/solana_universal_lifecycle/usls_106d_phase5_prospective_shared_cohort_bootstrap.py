from __future__ import annotations
import json,time
from pathlib import Path

BIRTH_PATH="runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"
TRADE_PATHS=[
 "runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json",
 "runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_universal_trade_rows.json",
 "runtime_state/solana_opportunities/universal_trade_tape/launchlab_universal_trade_rows.json",
]

def read(p):
 return json.loads(p.read_text(encoding="utf-8"))

def list_rows(d):
 for k in ("events","rows","exact_rows","trades"):
  if isinstance(d.get(k),list):return k,d[k]
 return None,[]

def sigs(rows):
 return {str(x.get("signature")) for x in rows if isinstance(x,dict) and x.get("signature")}

def birth_identity(x):
 return {"venue":x.get("launcher_family"),"program_id":x.get("program_id"),
  "token_address":x.get("token_address") or x.get("token_mint"),
  "market_address":x.get("pair_address"),
  "birth_signature":x.get("signature"),"birth_slot":x.get("slot"),
  "birth_observed_unix":x.get("observed_unix") or x.get("block_time")}

def build(root):
 root=Path(root)
 bp=root/BIRTH_PATH
 bd=read(bp);bk,br=list_rows(bd)
 now=time.time()
 last_slot=max([int(x.get("slot")) for x in br if isinstance(x,dict) and x.get("slot") is not None] or [0])
 last_time=max([float(x.get("observed_unix") or x.get("block_time")) for x in br
                if isinstance(x,dict) and (x.get("observed_unix") is not None or x.get("block_time") is not None)] or [0.0])
 trade_baselines=[]
 for rel in TRADE_PATHS:
  p=root/rel
  if not p.exists():
   trade_baselines.append({"path":rel,"exists":False,"row_count":0,"signatures":[]})
   continue
  d=read(p);k,rs=list_rows(d)
  trade_baselines.append({"path":rel,"exists":True,"revision":d.get("revision"),
   "list_key":k,"row_count":len(rs),"signatures":sorted(sigs(rs))})
 births=[birth_identity(x) for x in br if isinstance(x,dict)]
 return {"revision":"USLS_106D","phase":5,"bootstrap_unix":now,
  "birth_source":{"path":BIRTH_PATH,"revision":bd.get("revision"),"list_key":bk,
   "row_count":len(br),"last_slot":last_slot,"last_observed_unix":last_time},
  "trade_sources":trade_baselines,
  "birth_baseline_signatures":sorted(sigs(br)),
  "prospective_rule":"ONLY_BIRTHS_AND_TRADES_OBSERVED_AFTER_BOOTSTRAP_ARE_ELIGIBLE_FOR_SHARED_COHORT_JOIN",
  "identity_rule":"PROGRAM_TOKEN_MARKET_PREFERRED; VENUE_TOKEN_MARKET_ALLOWED_WHEN_PROGRAM_MISSING; NEVER_SIGNATURE_ONLY",
  "unknown_policy":"RETAIN_UNRESOLVED",
  "future_leakage_policy":"NO_PRE_BOOTSTRAP_TRADE_CAN_JOIN_POST_BOOTSTRAP_BIRTH",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_prospective_shared_cohort_bootstrap.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
