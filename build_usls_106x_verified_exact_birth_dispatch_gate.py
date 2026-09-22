from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106x_verified_exact_birth_dispatch_gate.py"
TEST=ROOT/"test_usls_106x_verified_exact_birth_dispatch_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"
OUT="runtime_state/solana_opportunities/solana_scanner/exact_birth_dispatch.json"
TARGETS={"PUMP_FUN","METEORA_DBC","METEORA_DAMM"}

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

def _family(r):
 n=r.get("raw_notification") or {}
 for k in ("family","venue","launcher_family","source_family"):
  v=_walk(n,k)
  if v not in (None,""):return str(v)
 return "UNKNOWN"

def _sig(r):
 return r.get("signature") or _walk(r.get("raw_notification") or {},"signature")

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

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def _tx(sig):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return await _maybe(_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
  "maxSupportedTransactionVersion":1}],20.0))

def _dispatch(family,tx):
 if family=="PUMP_FUN":
  from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _pump_ix
  hits=_pump_ix(tx) or []
  return {"exact_birth":bool(hits),"semantic":"PUMP_FUN_CREATE_V2",
          "instruction_count":len(hits),"instructions":hits}
 if family in ("METEORA_DBC","METEORA_DAMM"):
  from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067c_live_priority_rate_safe_birth_worker import _birth
  hit=bool(_birth(tx))
  return {"exact_birth":hit,"semantic":"METEORA_CERTIFIED_BIRTH_LOG_CONTRACT",
          "instruction_count":None,"instructions":[]}
 return {"exact_birth":False,"semantic":"NO_VERIFIED_EXACT_DECODER_DISPATCHED",
         "instruction_count":None,"instructions":[]}

async def probe(root,max_per_family=20):
 rows=_rows(root);by={k:[] for k in TARGETS}
 seen=set()
 for r in reversed(rows):
  fam=_family(r);sig=_sig(r)
  if fam not in TARGETS or _notif_err(r) is not None or not sig:continue
  key=(fam,str(sig))
  if key in seen:continue
  seen.add(key)
  if len(by[fam])<max_per_family:by[fam].append(r)
 probes=[];births=[]
 for fam in sorted(TARGETS):
  for r in by[fam]:
   sig=str(_sig(r));rec={"family":fam,"signature":sig,"slot":_slot(r),
     "rpc_error":None,"tx_found":False,"meta_err":None,"dispatch":None}
   try:
    tx=await _tx(sig)
    rec["tx_found"]=isinstance(tx,dict)
    if isinstance(tx,dict):
     rec["meta_err"]=(tx.get("meta") or {}).get("err")
     if rec["meta_err"] is None:
      rec["dispatch"]=_dispatch(fam,tx)
      if rec["dispatch"]["exact_birth"]:
       births.append({"family":fam,"signature":sig,"slot":tx.get("slot"),
        "block_time":tx.get("blockTime"),"observed_unix":r.get("scanner_observed_unix"),
        "semantic":rec["dispatch"]["semantic"],
        "instructions":rec["dispatch"]["instructions"],
        "raw_transaction":tx,"execution_authority":False})
   except Exception as e:rec["rpc_error"]=repr(e)
   probes.append(rec)
   await asyncio.sleep(0.75)
 return rows,by,probes,births

def run(root,max_per_family=20):
 rows,by,probes,births=asyncio.run(probe(root,max_per_family))
 dispatched=sum(1 for x in probes if x["dispatch"] is not None)
 rpc_errors=sum(x["rpc_error"] is not None for x in probes)
 return {"revision":"USLS_106X","source_revision":"USLS_106W",
  "raw_record_count":len(rows),
  "eligible_successful_candidates":{k:len(v) for k,v in by.items()},
  "dispatch_probe_count":len(probes),"successful_dispatch_count":dispatched,
  "rpc_error_count":rpc_errors,"exact_birth_count":len(births),
  "exact_births":births,"probes":probes,
  "pump_contract":"USLS_022._pump_ix(tx): exact create_v2 discriminator",
  "meteora_contract":"SULS_067C._birth(tx): certified DBC/DAMM birth log contract",
  "non_target_policy":"RETAIN_RAW_UNRESOLVED_NO_INVENTED_DECODER",
  "identity_materialization_certified":False,
  "lifecycle_join_certified":False,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root,max_per_family=20):
 d=run(root,max_per_family)
 p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106x_verified_exact_birth_dispatch_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_per_family=20)
  print("[STATE]",json.dumps({
   "raw_record_count":d["raw_record_count"],
   "eligible_successful_candidates":d["eligible_successful_candidates"],
   "dispatch_probe_count":d["dispatch_probe_count"],
   "successful_dispatch_count":d["successful_dispatch_count"],
   "rpc_error_count":d["rpc_error_count"],
   "exact_birth_count":d["exact_birth_count"]},sort_keys=True))
  for x in d["probes"]:
   print("[PROBE]",json.dumps({k:x[k] for k in ("family","signature","slot","rpc_error","tx_found","meta_err","dispatch")},sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(sum(d["eligible_successful_candidates"].values()),0,"NO_SUCCESSFUL_TARGET_FAMILY_CANDIDATES")
  self.assertGreater(d["dispatch_probe_count"],0,"NO_EXACT_DECODER_DISPATCH_ATTEMPTED")
  self.assertGreater(d["successful_dispatch_count"],0,"NO_VERIFIED_DECODER_EXECUTED")
  self.assertEqual(d["non_target_policy"],"RETAIN_RAW_UNRESOLVED_NO_INVENTED_DECODER")
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106X verified exact-birth dispatch gate")
  if d["exact_birth_count"]:
   print("[READY] exact prospective birth semantics detected; identity materialization is next")
  else:
   print("[WAIT] verified decoders executed; no exact birth in retained bounded cohort")
  print("[PASS] non-target families retained unresolved; no decoder invented")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
