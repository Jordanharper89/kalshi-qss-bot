from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106u_scanner_notification_success_prefilter_hydration_gate.py"
TEST=ROOT/"test_usls_106u_scanner_notification_success_prefilter_hydration_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"

def _rows(root):
 p=Path(root)/RAW;out=[]
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():out.append(json.loads(line))
 return out

def _walk(x,key):
 if isinstance(x,dict):
  if key in x:return x.get(key)
  for v in x.values():
   y=_walk(v,key)
   if y is not None:return y
 elif isinstance(x,list):
  for v in x:
   y=_walk(v,key)
   if y is not None:return y
 return None

def _sig(r):
 return r.get("signature") or _walk(r.get("raw_notification") or {},"signature")

def _family(r):
 n=r.get("raw_notification") or {}
 for k in ("family","venue","launcher_family","source_family"):
  v=_walk(n,k)
  if v not in (None,""):return str(v)
 return "UNKNOWN"

def _notif_err(r):
 n=r.get("raw_notification") or {}
 # Solana logsSubscribe normally stores transaction failure under value.err.
 v=n.get("value")
 if isinstance(v,dict) and "err" in v:return v.get("err")
 result=n.get("result")
 if isinstance(result,dict):
  vv=result.get("value")
  if isinstance(vv,dict) and "err" in vv:return vv.get("err")
 if "err" in n:return n.get("err")
 return _walk(n,"err")

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def _hydrate(sig,slot=None):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import _hydrate
 return await _maybe(_hydrate(sig,slot,time.time()))

async def probe(root,max_hydrations=5):
 rows=_rows(root);successful=[];failed=[];unknown=[]
 for r in rows:
  e=_notif_err(r)
  item=(r,_sig(r),_family(r),_walk(r.get("raw_notification") or {},"slot"),e)
  if e is None:successful.append(item)
  else:failed.append(item)
 # hydrate distinct successful signatures only
 seen=set();cands=[]
 for item in reversed(successful):
  s=item[1]
  if s and s not in seen:
   seen.add(s);cands.append(item)
  if len(cands)>=max_hydrations:break
 probes=[];hydrated=[]
 for i,(r,s,fam,slot,e) in enumerate(cands):
  rec={"signature":s,"family":fam,"slot":slot,"error":None,"hydrated_type":None}
  try:
   h=await _hydrate(s,slot)
   rec["hydrated_type"]=type(h).__name__
   if isinstance(h,dict):hydrated.append(h)
  except Exception as ex:rec["error"]=repr(ex)
  probes.append(rec)
  if i+1<len(cands):await asyncio.sleep(1.5)
 return rows,successful,failed,probes,hydrated

def run(root,max_hydrations=5):
 rows,successful,failed,probes,hydrated=asyncio.run(probe(root,max_hydrations))
 fam={}
 for r in rows:
  f=_family(r);fam.setdefault(f,{"total":0,"notification_success":0,"notification_failed":0})
  fam[f]["total"]+=1
  if _notif_err(r) is None:fam[f]["notification_success"]+=1
  else:fam[f]["notification_failed"]+=1
 return {"revision":"USLS_106U","source_revision":"USLS_106T",
  "raw_record_count":len(rows),"notification_success_count":len(successful),
  "notification_failed_count":len(failed),"family_outcomes":fam,
  "hydration_probe_count":len(probes),"hydrated_ok":len(hydrated),"probes":probes,
  "finding":("SUCCESSFUL_NOTIFICATION_PREFILTER_AND_HYDRATION_PROVEN"
             if hydrated else
             "NO_SUCCESSFUL_NOTIFICATION_HYDRATED"),
  "failed_notification_policy":"RETAIN_RAW_ACTIVITY_EXCLUDE_FROM_EXACT_BIRTH_CERTIFICATION",
  "next_boundary":"EXACT_BIRTH_DECODING_FROM_SUCCESSFUL_HYDRATED_RAW_ACTIVITY",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_hydrations=5):
 d=run(root,max_hydrations)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_notification_success_prefilter_hydration_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106u_scanner_notification_success_prefilter_hydration_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_hydrations=5)
  print("[STATE]",json.dumps({
   "raw_record_count":d["raw_record_count"],
   "notification_success_count":d["notification_success_count"],
   "notification_failed_count":d["notification_failed_count"],
   "hydration_probe_count":d["hydration_probe_count"],
   "hydrated_ok":d["hydrated_ok"],
   "finding":d["finding"]},sort_keys=True))
  print("[FAMILY_OUTCOMES]",json.dumps(d["family_outcomes"],sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["notification_success_count"],0,"NO_SUCCESSFUL_LOGS_SUBSCRIBE_NOTIFICATION_PRESENT")
  self.assertGreater(d["hydration_probe_count"],0,"NO_SUCCESSFUL_SIGNATURES_SELECTED_FOR_HYDRATION")
  self.assertGreater(d["hydrated_ok"],0,"SUCCESSFUL_NOTIFICATION_DID_NOT_HYDRATE")
  self.assertEqual(d["failed_notification_policy"],
   "RETAIN_RAW_ACTIVITY_EXCLUDE_FROM_EXACT_BIRTH_CERTIFICATION")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106U notification-success prefilter hydration gate")
  print("[PASS] failed transactions retained raw; successful notifications selected before RPC hydration")
  print("[NEXT] EXACT_BIRTH_DECODING_FROM_SUCCESSFUL_HYDRATED_RAW_ACTIVITY")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
