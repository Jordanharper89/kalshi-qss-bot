from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106i_separate_scanner_dual_lane_physical_probe.py"
TEST=ROOT/"test_usls_106i_separate_scanner_dual_lane_physical_probe.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106i_separate_scanner_dual_lane_physical_probe import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT,seconds=12,max_rows=2000)
  print("[STATE]",json.dumps({
   "runtime":d["runtime"],
   "elapsed_seconds":round(d["elapsed_seconds"],3),
   "birth_lane":d["birth_lane"],
   "birth_before_count":d["birth_before_count"],
   "birth_after_count":d["birth_after_count"],
   "new_birth_count":d["new_birth_count"],
   "trade_return_type":d["trade_return_type"],
   "trade_row_count":d["trade_row_count"],
   "trade_lane_error":d["trade_lane_error"]},sort_keys=True))
  self.assertTrue(d["birth_lane"]["started"])
  self.assertIsNone(d["trade_lane_error"],"TRADE_LANE_PHYSICAL_CAPTURE_FAILED")
  self.assertGreater(d["trade_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY_CAPTURED")
  self.assertFalse(d["production_activation_claimed"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106I separate Solana Scanner dual-lane physical probe")
  print("[PASS] live universal trade acquisition physically active")
  print("[PASS] birth lane invoked concurrently; join remains uncertified")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
