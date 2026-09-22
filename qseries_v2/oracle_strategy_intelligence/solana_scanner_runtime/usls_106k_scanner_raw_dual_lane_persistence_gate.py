from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106j_separate_scanner_async_dual_lane_physical_probe import run as dual_run

def _canon(x):
 return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def _id(kind,payload):
 sig=payload.get("signature") if isinstance(payload,dict) else None
 venue=payload.get("venue") if isinstance(payload,dict) else None
 market=payload.get("market_address") if isinstance(payload,dict) else None
 base=f"{kind}|{sig}|{venue}|{market}|{_canon(payload)}"
 return hashlib.sha256(base.encode("utf-8")).hexdigest()

def _load_ids(path):
 out=set()
 if not path.exists():return out
 for line in path.read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  try:out.add(json.loads(line)["record_id"])
  except Exception:continue
 return out

def run(root,seconds=12,max_rows=2000):
 root=Path(root)
 state=dual_run(root,seconds=seconds,max_rows=max_rows)
 d=root/"runtime_state/solana_opportunities/solana_scanner"
 d.mkdir(parents=True,exist_ok=True)
 tape=d/"raw_birth_trade_tape.jsonl"
 seen=_load_ids(tape)
 now=time.time();records=[];dupes=0
 for kind,rows in (("BIRTH",state.get("new_births") or []),("TRADE",state.get("trade_rows") or [])):
  for payload in rows:
   rid=_id(kind,payload)
   if rid in seen:
    dupes+=1;continue
   seen.add(rid)
   records.append({"record_id":rid,"record_type":kind,"scanner_observed_unix":now,
    "payload":payload,"execution_authority":False})
 if records:
  with tape.open("a",encoding="utf-8") as f:
   for r in records:f.write(_canon(r)+"\n")
 births=sum(r["record_type"]=="BIRTH" for r in records)
 trades=sum(r["record_type"]=="TRADE" for r in records)
 return {"revision":"USLS_106K","source_revision":"USLS_106J",
  "session_trade_rows":len(state.get("trade_rows") or []),
  "session_new_births":len(state.get("new_births") or []),
  "persisted_birth_rows":births,"persisted_trade_rows":trades,
  "deduplicated_existing_rows":dupes,"tape_path":str(tape.relative_to(root)),
  "birth_lane":state.get("birth_lane"),"trade_lane_error":state.get("trade_lane_error"),
  "raw_retention":True,"unknown_retention":"RETAIN_RAW_UNRESOLVED",
  "restart_safe_append":True,"lifecycle_join_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,seconds=12,max_rows=2000):
 d=run(root,seconds,max_rows)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_raw_dual_lane_persistence_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
