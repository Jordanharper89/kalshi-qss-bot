from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106y_rate_safe_exact_birth_retry_gate.py"
TEST=ROOT/"test_usls_106y_rate_safe_exact_birth_retry_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/exact_birth_dispatch.json"
OUT="runtime_state/solana_opportunities/solana_scanner/exact_birth_retry.json"

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def _rpc_tx(sig):
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

async def _retry_one(item,max_attempts=3):
 sig=item["signature"];fam=item["family"]
 attempts=[];birth=None
 for n in range(1,max_attempts+1):
  rec={"attempt":n,"rpc_error":None,"tx_found":False,"meta_err":None,"dispatch":None}
  try:
   tx=await _rpc_tx(sig)
   rec["tx_found"]=isinstance(tx,dict)
   if isinstance(tx,dict):
    rec["meta_err"]=(tx.get("meta") or {}).get("err")
    if rec["meta_err"] is None:
     rec["dispatch"]=_dispatch(fam,tx)
     if rec["dispatch"]["exact_birth"]:
      birth={"family":fam,"signature":sig,"slot":tx.get("slot"),
       "block_time":tx.get("blockTime"),"semantic":rec["dispatch"]["semantic"],
       "instructions":rec["dispatch"]["instructions"],"raw_transaction":tx,
       "execution_authority":False}
     attempts.append(rec)
     break
  except Exception as e:
   rec["rpc_error"]=repr(e)
  attempts.append(rec)
  if n<max_attempts:
   await asyncio.sleep(3.0*(2**(n-1)))
 return {"family":fam,"signature":sig,"attempts":attempts,
         "resolved":any(a["dispatch"] is not None for a in attempts),
         "exact_birth":birth}

async def retry(root,max_attempts=3,max_items=14):
 src=Path(root)/SRC
 d=json.loads(src.read_text(encoding="utf-8"))
 pending=[x for x in d.get("probes",[]) if x.get("rpc_error")]
 pending=pending[:max_items]
 out=[]
 for i,item in enumerate(pending):
  out.append(await _retry_one(item,max_attempts))
  if i+1<len(pending):await asyncio.sleep(2.5)
 return d,pending,out

def run(root,max_attempts=3,max_items=14):
 prior,pending,retries=asyncio.run(retry(root,max_attempts,max_items))
 recovered=sum(x["resolved"] for x in retries)
 births=[x["exact_birth"] for x in retries if x["exact_birth"]]
 still=sum(not x["resolved"] for x in retries)
 return {"revision":"USLS_106Y","source_revision":"USLS_106X",
  "prior_rpc_error_count":prior.get("rpc_error_count"),
  "retry_candidate_count":len(pending),"recovered_dispatch_count":recovered,
  "still_unresolved_count":still,"exact_birth_count":len(births),
  "exact_births":births,"retries":retries,
  "rate_safe_retry":True,"backoff_seconds":[3.0,6.0],
  "identity_materialization_certified":False,
  "lifecycle_join_certified":False,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root,max_attempts=3,max_items=14):
 d=run(root,max_attempts,max_items)
 p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106y_rate_safe_exact_birth_retry_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_attempts=3,max_items=14)
  print("[STATE]",json.dumps({
   "prior_rpc_error_count":d["prior_rpc_error_count"],
   "retry_candidate_count":d["retry_candidate_count"],
   "recovered_dispatch_count":d["recovered_dispatch_count"],
   "still_unresolved_count":d["still_unresolved_count"],
   "exact_birth_count":d["exact_birth_count"]},sort_keys=True))
  for x in d["retries"]:
   print("[RETRY]",json.dumps({
    "family":x["family"],"signature":x["signature"],"resolved":x["resolved"],
    "attempts":x["attempts"]},sort_keys=True))
  self.assertGreater(d["retry_candidate_count"],0,"NO_106X_RPC_ERRORS_TO_RETRY")
  self.assertTrue(d["rate_safe_retry"])
  self.assertGreater(d["recovered_dispatch_count"],0,"NO_RATE_LIMITED_DISPATCH_RECOVERED")
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106Y rate-safe exact-birth retry gate")
  if d["exact_birth_count"]:
   print("[READY] exact birth recovered from previously rate-limited cohort")
  else:
   print("[WAIT] rate-limited cohort recovered; no exact birth in recovered transactions")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
