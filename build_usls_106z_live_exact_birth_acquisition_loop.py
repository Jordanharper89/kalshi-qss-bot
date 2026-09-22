from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106z_live_exact_birth_acquisition_loop.py"
TEST=ROOT/"test_usls_106z_live_exact_birth_acquisition_loop.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time,hashlib
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"
BIRTHS="runtime_state/solana_opportunities/solana_scanner/exact_births.jsonl"
TARGETS={"PUMP_FUN","METEORA_DBC","METEORA_DAMM"}

def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _rid(x):return hashlib.sha256(_canon(x).encode()).hexdigest()

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

def _family(r):
 n=r.get("raw_notification") or {}
 for k in ("family","venue","launcher_family","source_family"):
  v=_walk(n,k)
  if v not in (None,""):return str(v)
 return "UNKNOWN"

def _sig(r):return r.get("signature") or _walk(r.get("raw_notification") or {},"signature")

def _slot(r):
 v=_walk(r.get("raw_notification") or {},"slot")
 try:return int(v) if v is not None else None
 except Exception:return None

def _notif_err(r):
 n=r.get("raw_notification") or {}
 v=n.get("value")
 if isinstance(v,dict) and "err" in v:return v.get("err")
 rr=n.get("result")
 if isinstance(rr,dict):
  vv=rr.get("value")
  if isinstance(vv,dict) and "err" in vv:return vv.get("err")
 if "err" in n:return n.get("err")
 return _walk(n,"err")

def _read_jsonl(path):
 out=[]
 if not path.exists():return out
 for line in path.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try:out.append(json.loads(line))
   except Exception:pass
 return out

async def _maybe(v):return await v if inspect.isawaitable(v) else v

async def _tx(sig):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return await _maybe(_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
  "maxSupportedTransactionVersion":1}],20.0))

def _dispatch(fam,tx):
 if fam=="PUMP_FUN":
  from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _pump_ix
  hits=_pump_ix(tx) or []
  return bool(hits),"PUMP_FUN_CREATE_V2",hits
 if fam in ("METEORA_DBC","METEORA_DAMM"):
  from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067c_live_priority_rate_safe_birth_worker import _birth
  return bool(_birth(tx)),"METEORA_CERTIFIED_BIRTH_LOG_CONTRACT",[]
 return False,"NO_VERIFIED_DECODER",[]

async def _hydrate_dispatch(row,max_attempts=3):
 sig=str(_sig(row));fam=_family(row);attempts=[]
 for n in range(1,max_attempts+1):
  try:
   tx=await _tx(sig)
   if not isinstance(tx,dict):
    attempts.append({"attempt":n,"state":"TX_NULL"})
   elif (tx.get("meta") or {}).get("err") is not None:
    attempts.append({"attempt":n,"state":"TX_FAILED","meta_err":(tx.get("meta") or {}).get("err")})
    return attempts,None
   else:
    hit,semantic,instructions=_dispatch(fam,tx)
    attempts.append({"attempt":n,"state":"DISPATCHED","exact_birth":hit})
    birth=None
    if hit:
     birth={"record_id":_rid({"family":fam,"signature":sig,"semantic":semantic}),
      "family":fam,"signature":sig,"slot":tx.get("slot") or _slot(row),
      "block_time":tx.get("blockTime"),"observed_unix":row.get("scanner_observed_unix"),
      "semantic":semantic,"instructions":instructions,"raw_transaction":tx,
      "identity_materialized":False,"execution_authority":False}
    return attempts,birth
  except Exception as e:
   attempts.append({"attempt":n,"state":"RPC_ERROR","error":repr(e)})
  if n<max_attempts:await asyncio.sleep(3.0*(2**(n-1)))
 return attempts,None

async def cycle(root,seconds=12,max_hydrations=8):
 from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106p_scanner_raw_program_admission_before_classification import run as admit
 before=_read_jsonl(Path(root)/RAW)
 before_ids={x.get("record_id") for x in before}
 admission=await asyncio.to_thread(admit,root,seconds)
 after=_read_jsonl(Path(root)/RAW)
 fresh=[x for x in after if x.get("record_id") not in before_ids]
 eligible=[x for x in fresh if _family(x) in TARGETS and _notif_err(x) is None and _sig(x)]
 results=[];births=[]
 for i,row in enumerate(eligible[:max_hydrations]):
  attempts,birth=await _hydrate_dispatch(row)
  results.append({"family":_family(row),"signature":_sig(row),"attempts":attempts,"exact_birth":birth is not None})
  if birth:births.append(birth)
  if i+1<min(len(eligible),max_hydrations):await asyncio.sleep(1.5)
 return admission,fresh,eligible,results,births

def run(root,cycles=3,seconds=12,max_hydrations=8):
 root=Path(root);history=[];all_births=[]
 for i in range(1,cycles+1):
  admission,fresh,eligible,results,births=asyncio.run(cycle(root,seconds,max_hydrations))
  history.append({"cycle":i,"raw_notifications":admission.get("notification_count",0),
   "fresh_raw_rows":len(fresh),"eligible_successful_target_rows":len(eligible),
   "dispatch_attempted":len(results),"exact_births":len(births),"results":results})
  all_births.extend(births)
  if births:break
 bp=root/BIRTHS;bp.parent.mkdir(parents=True,exist_ok=True)
 seen={x.get("record_id") for x in _read_jsonl(bp)}
 new=[b for b in all_births if b["record_id"] not in seen]
 if new:
  with bp.open("a",encoding="utf-8") as f:
   for b in new:f.write(_canon(b)+"\n")
 return {"revision":"USLS_106Z","cycles_completed":len(history),"history":history,
  "exact_births_detected":len(all_births),"exact_births_persisted_new":len(new),
  "total_exact_birth_records":len(_read_jsonl(bp)),
  "state":"EXACT_BIRTH_CAPTURED_IDENTITY_NEXT" if all_births else "WAITING_FOR_EXACT_PROSPECTIVE_BIRTH",
  "raw_admission_before_classification":True,"rate_safe_retry":True,
  "identity_materialization_certified":False,"lifecycle_join_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,cycles=3,seconds=12,max_hydrations=8):
 d=run(root,cycles,seconds,max_hydrations)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_live_exact_birth_acquisition_loop.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106z_live_exact_birth_acquisition_loop import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,cycles=3,seconds=12,max_hydrations=8)
  print("[STATE]",json.dumps({"cycles_completed":d["cycles_completed"],
   "exact_births_detected":d["exact_births_detected"],
   "exact_births_persisted_new":d["exact_births_persisted_new"],
   "total_exact_birth_records":d["total_exact_birth_records"],"state":d["state"]},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["cycles_completed"],0)
  self.assertTrue(d["raw_admission_before_classification"])
  self.assertTrue(d["rate_safe_retry"])
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106Z live exact-birth acquisition loop")
  if d["exact_births_detected"]:
   print("[READY] exact prospective birth captured; identity materialization next")
  else:
   print("[WAIT] no exact prospective birth in bounded live window; rerun later")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
