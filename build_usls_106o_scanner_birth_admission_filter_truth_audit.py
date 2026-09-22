from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106o_scanner_birth_admission_filter_truth_audit.py"
TEST=ROOT/"test_usls_106o_scanner_birth_admission_filter_truth_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,re,time
from pathlib import Path

S083="qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_083_persistent_event_driven_runtime.py"
F076="qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_076_birth_log_notification_filter.py"
P011="qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner/usls_011_live_14_program_websocket_probe.py"

def _src(root,rel):
 p=Path(root)/rel
 return p.read_text(encoding="utf-8",errors="ignore") if p.exists() else ""

def static_audit(root):
 s083=_src(root,S083);f076=_src(root,F076)
 return {
  "s083_exists":bool(s083),"filter_exists":bool(f076),
  "s083_imports_birth_filter":("suls_076_birth_log_notification_filter" in s083),
  "s083_calls_is_birth":bool(re.search(r"\bis_birth\s*\(",s083)),
  "s083_continue_on_filter":bool(re.search(r"if\s+not\s+is_birth\s*\([^)]*\)\s*:\s*(?:\n\s*)?continue",s083)),
  "filter_family_terms":sorted(set(re.findall(r"(METEORA|PUMP|RAYDIUM|ORCA|MOONIT|BOOP|HEAVEN)",f076,re.I))),
  "filter_source_excerpt":[ln.strip() for ln in f076.splitlines() if "birth" in ln.lower() or "log" in ln.lower()][:60]
 }

async def _call(fn,*args,**kwargs):
 v=fn(*args,**kwargs)
 return await v if inspect.isawaitable(v) else v

def _shape(v):
 if isinstance(v,dict):
  return {"type":"dict","keys":sorted(v.keys())[:80],
   "list_shapes":[{"key":k,"len":len(x)} for k,x in v.items() if isinstance(x,list)]}
 if isinstance(v,list): return {"type":"list","len":len(v)}
 return {"type":type(v).__name__}

async def live_probe(root,seconds=12):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_011_live_14_program_websocket_probe import probe
 started=time.time();err=None;ret=None
 try:ret=await _call(probe,root,seconds=seconds)
 except Exception as e:err=repr(e)
 artifact=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_14_program_probe.json"
 art=None
 if artifact.exists():
  try:art=json.loads(artifact.read_text(encoding="utf-8"))
  except Exception:pass
 return {"elapsed_seconds":time.time()-started,"error":err,"return_shape":_shape(ret),
  "artifact_exists":artifact.exists(),"artifact_shape":_shape(art) if art is not None else None,
  "artifact":art}

def run(root,seconds=12):
 static=static_audit(root)
 live=asyncio.run(live_probe(root,seconds))
 suspicious=bool(static["s083_imports_birth_filter"] and static["s083_calls_is_birth"])
 return {"revision":"USLS_106O","static":static,"live":live,
  "finding":"SULS083_FILTERED_BIRTH_LANE_NOT_UNIVERSAL_RAW_ADMISSION" if suspicious else "FILTER_PATH_NOT_CONFIRMED",
  "required_repair":"SCANNER_OWNED_RAW_KNOWN_PROGRAM_ADMISSION_BEFORE_BIRTH_CLASSIFICATION",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,seconds=12):
 d=run(root,seconds)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_birth_admission_filter_truth_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106o_scanner_birth_admission_filter_truth_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT,seconds=12)
  s=d["static"];l=d["live"]
  print("[STATE]",json.dumps({"finding":d["finding"],"required_repair":d["required_repair"],
   "s083_imports_birth_filter":s["s083_imports_birth_filter"],"s083_calls_is_birth":s["s083_calls_is_birth"],
   "s083_continue_on_filter":s["s083_continue_on_filter"],"filter_family_terms":s["filter_family_terms"],
   "live_error":l["error"],"live_return_shape":l["return_shape"],
   "artifact_exists":l["artifact_exists"],"artifact_shape":l["artifact_shape"],
   "elapsed_seconds":round(l["elapsed_seconds"],3)},sort_keys=True))
  self.assertTrue(s["s083_exists"],"SULS083_MISSING")
  self.assertTrue(s["filter_exists"],"SULS076_FILTER_MISSING")
  self.assertTrue(s["s083_imports_birth_filter"],"SULS083_FILTER_IMPORT_NOT_FOUND")
  self.assertTrue(s["s083_calls_is_birth"],"SULS083_FILTER_CALL_NOT_FOUND")
  self.assertIsNone(l["error"],"UNIVERSAL_14_PROGRAM_PROBE_FAILED")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106O scanner birth-admission filter truth audit")
  print("[PASS] filtered SULS-083 lane distinguished from universal raw scanner admission")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
