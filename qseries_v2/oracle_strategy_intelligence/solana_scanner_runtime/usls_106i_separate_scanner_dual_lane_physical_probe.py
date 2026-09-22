from __future__ import annotations
import json,threading,time,traceback
from pathlib import Path

BIRTH_FILE="runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"

def _read_births(root):
 p=Path(root)/BIRTH_FILE
 if not p.exists(): return []
 try:
  d=json.loads(p.read_text(encoding="utf-8"))
 except Exception:
  return []
 for k in ("events","births","rows"):
  if isinstance(d.get(k),list): return d[k]
 return []

def _sigs(rows):
 return {str(x.get("signature")) for x in rows if isinstance(x,dict) and x.get("signature")}

def _trade_rows(v):
 if isinstance(v,list): return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list): return v[k]
 return []

def run(root,seconds=12,max_rows=2000):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import serve
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture

 before=_read_births(root); before_sigs=_sigs(before)
 birth_state={"started":False,"completed":False,"error":None}
 def birth_lane():
  birth_state["started"]=True
  try:
   serve(root,max_seconds=seconds)
   birth_state["completed"]=True
  except Exception as e:
   birth_state["error"]=repr(e)

 t=threading.Thread(target=birth_lane,name="solana-scanner-birth-lane",daemon=True)
 t.start()
 started=time.time()
 trade_error=None
 trade_obj=None
 try:
  trade_obj=capture(seconds=seconds,max_rows=max_rows)
 except Exception as e:
  trade_error=repr(e)
 t.join(timeout=seconds+8)
 elapsed=time.time()-started

 after=_read_births(root); after_sigs=_sigs(after)
 new_births=[x for x in after if isinstance(x,dict) and str(x.get("signature")) in (after_sigs-before_sigs)]
 trades=_trade_rows(trade_obj)

 return {
  "revision":"USLS_106I",
  "runtime":"SOLANA_SCANNER_SEPARATE_BOUNDED_PROBE",
  "seconds_requested":seconds,
  "elapsed_seconds":elapsed,
  "birth_lane":birth_state,
  "birth_before_count":len(before),
  "birth_after_count":len(after),
  "new_birth_count":len(new_births),
  "new_births":new_births,
  "trade_lane_error":trade_error,
  "trade_return_type":type(trade_obj).__name__,
  "trade_row_count":len(trades),
  "trade_rows":trades,
  "raw_known_program_retention":True,
  "unknown_retention":"RETAIN_RAW_UNRESOLVED",
  "production_activation_claimed":False,
  "lifecycle_join_certified":False,
  "profitability_claimed":False,
  "execution_authority":False,
  "read_only":True
 }

def write(root,seconds=12,max_rows=2000):
 d=run(root,seconds,max_rows)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_dual_lane_physical_probe.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
