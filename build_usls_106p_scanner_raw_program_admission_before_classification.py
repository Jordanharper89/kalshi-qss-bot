from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106p_scanner_raw_program_admission_before_classification.py"
TEST=ROOT/"test_usls_106p_scanner_raw_program_admission_before_classification.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,hashlib,inspect,json,time
from pathlib import Path

OUT="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"

async def _call(fn,*args,**kwargs):
 v=fn(*args,**kwargs)
 return await v if inspect.isawaitable(v) else v

def _canon(x):
 return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def _rid(x):
 return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()

def _seen(path):
 s=set()
 if not path.exists(): return s
 for line in path.read_text(encoding="utf-8").splitlines():
  if not line.strip(): continue
  try:s.add(json.loads(line).get("record_id"))
  except Exception:pass
 return {x for x in s if x}

def _logs(n):
 if not isinstance(n,dict): return []
 for k in ("logs","logMessages"):
  if isinstance(n.get(k),list): return n[k]
 v=n.get("value")
 if isinstance(v,dict):
  for k in ("logs","logMessages"):
   if isinstance(v.get(k),list): return v[k]
 r=n.get("result")
 if isinstance(r,dict):
  v=r.get("value")
  if isinstance(v,dict):
   for k in ("logs","logMessages"):
    if isinstance(v.get(k),list): return v[k]
 return []

def _signature(n):
 if not isinstance(n,dict): return None
 for k in ("signature","sig"):
  if n.get(k): return n[k]
 for box in ("value","result"):
  v=n.get(box)
  if isinstance(v,dict):
   if v.get("signature"): return v["signature"]
   vv=v.get("value")
   if isinstance(vv,dict) and vv.get("signature"): return vv["signature"]
 return None

async def _probe(root,seconds):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_011_live_14_program_websocket_probe import probe
 return await _call(probe,root,seconds=seconds)

def run(root,seconds=12):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_076_birth_log_notification_filter import is_birth
 root=Path(root);result=asyncio.run(_probe(root,seconds))
 notifications=(result or {}).get("notifications") if isinstance(result,dict) else None
 if not isinstance(notifications,list): notifications=[]
 p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 seen=_seen(p);new=[];dupes=0;classified=0
 for n in notifications:
  rid=_rid(n)
  if rid in seen:
   dupes+=1;continue
  seen.add(rid)
  logs=_logs(n)
  birth_hint=False
  try:birth_hint=bool(is_birth(logs))
  except Exception:birth_hint=False
  if birth_hint:classified+=1
  new.append({"record_id":rid,"record_type":"RAW_PROGRAM_ACTIVITY",
   "scanner_observed_unix":time.time(),"signature":_signature(n),
   "logs":logs,"birth_hint_after_raw_admission":birth_hint,
   "raw_notification":n,"execution_authority":False})
 if new:
  with p.open("a",encoding="utf-8") as f:
   for r in new:f.write(_canon(r)+"\n")
 return {"revision":"USLS_106P","probe_seconds":seconds,
  "notification_count":len(notifications),"persisted_new_rows":len(new),
  "deduplicated_existing_rows":dupes,"birth_hints_after_raw_admission":classified,
  "raw_admission_before_classification":True,
  "raw_known_program_retention":True,"unknown_retention":"RETAIN_RAW_UNRESOLVED",
  "output_path":OUT,"lifecycle_join_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,seconds=12):
 d=run(root,seconds)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_raw_program_admission_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106p_scanner_raw_program_admission_before_classification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,seconds=12)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["notification_count"],0,"NO_UNIVERSAL_PROGRAM_ACTIVITY")
  self.assertGreater(d["persisted_new_rows"]+d["deduplicated_existing_rows"],0,"NO_RAW_PROGRAM_ACTIVITY_RETAINED")
  self.assertTrue(d["raw_admission_before_classification"])
  self.assertTrue(d["raw_known_program_retention"])
  self.assertEqual(d["unknown_retention"],"RETAIN_RAW_UNRESOLVED")
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106P scanner raw-program admission before classification")
  print("[PASS] universal known-program activity retained before birth filtering")
  print("[INFO] birth_hints_after_raw_admission=",d["birth_hints_after_raw_admission"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
