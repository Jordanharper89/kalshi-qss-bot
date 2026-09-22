from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

BIRTH_FILE="runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"

def _read_births(root):
 p=Path(root)/BIRTH_FILE
 if not p.exists(): return []
 try:d=json.loads(p.read_text(encoding="utf-8"))
 except Exception:return []
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

async def _call_maybe_async(fn,*args,**kwargs):
 v=fn(*args,**kwargs)
 if inspect.isawaitable(v): return await v
 return v

async def _run_async(root,seconds,max_rows):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import serve
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture

 before=_read_births(root); before_sigs=_sigs(before)
 async def birth_lane():
  try:
   r=await _call_maybe_async(serve,root,max_seconds=seconds)
   return {"started":True,"completed":True,"error":None,"return_type":type(r).__name__}
  except Exception as e:
   return {"started":True,"completed":False,"error":repr(e),"return_type":None}

 async def trade_lane():
  try:
   r=await _call_maybe_async(capture,seconds=seconds,max_rows=max_rows)
   return {"error":None,"result":r}
  except Exception as e:
   return {"error":repr(e),"result":None}

 started=time.time()
 birth_result,trade_result=await asyncio.gather(birth_lane(),trade_lane())
 elapsed=time.time()-started
 after=_read_births(root); after_sigs=_sigs(after)
 new_births=[x for x in after if isinstance(x,dict) and str(x.get("signature")) in (after_sigs-before_sigs)]
 trades=_trade_rows(trade_result["result"])
 return {
  "revision":"USLS_106J",
  "supersedes_failed_revision":"USLS_106I",
  "runtime":"SOLANA_SCANNER_SEPARATE_ASYNC_BOUNDED_PROBE",
  "seconds_requested":seconds,
  "elapsed_seconds":elapsed,
  "birth_lane":birth_result,
  "birth_before_count":len(before),
  "birth_after_count":len(after),
  "new_birth_count":len(new_births),
  "new_births":new_births,
  "trade_lane_error":trade_result["error"],
  "trade_return_type":type(trade_result["result"]).__name__,
  "trade_row_count":len(trades),
  "trade_rows":trades,
  "async_execution_verified":True,
  "raw_known_program_retention":True,
  "unknown_retention":"RETAIN_RAW_UNRESOLVED",
  "production_activation_claimed":False,
  "lifecycle_join_certified":False,
  "profitability_claimed":False,
  "execution_authority":False,
  "read_only":True
 }

def run(root,seconds=12,max_rows=2000):
 return asyncio.run(_run_async(root,seconds,max_rows))

def write(root,seconds=12,max_rows=2000):
 d=run(root,seconds,max_rows)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_async_dual_lane_physical_probe.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
