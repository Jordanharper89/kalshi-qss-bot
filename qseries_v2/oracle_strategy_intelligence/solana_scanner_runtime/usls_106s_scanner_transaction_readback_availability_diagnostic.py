from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"

def _walk(x,key):
 if isinstance(x,dict):
  if x.get(key) not in (None,""):return x.get(key)
  for v in x.values():
   y=_walk(v,key)
   if y not in (None,""):return y
 elif isinstance(x,list):
  for v in x:
   y=_walk(v,key)
   if y not in (None,""):return y
 return None

def _rows(root):
 p=Path(root)/RAW;out=[]
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():out.append(json.loads(line))
 return out

def _sig(row):
 return row.get("signature") or _walk(row.get("raw_notification") or {},"signature")

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def _rpc_call(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return await _maybe(_rpc(method,params,timeout))

async def probe(root,max_samples=2):
 rows=_rows(root);sigs=[];seen=set()
 for r in reversed(rows):
  s=_sig(r)
  if s and s not in seen:
   seen.add(s);sigs.append(str(s))
  if len(sigs)>=max_samples:break
 out=[]
 for s in sigs:
  item={"signature":s,"status":None,"confirmed_attempts":[],"finalized_attempt":None}
  try:
   item["status"]=await _rpc_call("getSignatureStatuses",[[s],{"searchTransactionHistory":True}],20.0)
  except Exception as e:
   item["status_error"]=repr(e)
  for delay in (0.0,2.0,5.0):
   if delay:await asyncio.sleep(delay)
   rec={"delay_seconds":delay,"error":None,"result_type":None,"is_null":None,"slot":None,"meta_err":None}
   try:
    r=await _rpc_call("getTransaction",[s,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
    rec["result_type"]=type(r).__name__;rec["is_null"]=r is None
    if isinstance(r,dict):
     rec["slot"]=r.get("slot");rec["meta_err"]=(r.get("meta") or {}).get("err")
   except Exception as e:rec["error"]=repr(e)
   item["confirmed_attempts"].append(rec)
   if rec["error"] is None and rec["is_null"] is False:break
  if all(x["is_null"] is not False for x in item["confirmed_attempts"] if x["error"] is None):
   await asyncio.sleep(2.0)
   rec={"error":None,"result_type":None,"is_null":None,"slot":None,"meta_err":None}
   try:
    r=await _rpc_call("getTransaction",[s,{"commitment":"finalized","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
    rec["result_type"]=type(r).__name__;rec["is_null"]=r is None
    if isinstance(r,dict):
     rec["slot"]=r.get("slot");rec["meta_err"]=(r.get("meta") or {}).get("err")
   except Exception as e:rec["error"]=repr(e)
   item["finalized_attempt"]=rec
  out.append(item)
  await asyncio.sleep(2.0)
 return rows,out

def classify(probes):
 any_status=False;any_tx=False;any_429=False
 for p in probes:
  st=p.get("status")
  vals=(st or {}).get("value") if isinstance(st,dict) else None
  if isinstance(vals,list) and any(v for v in vals):any_status=True
  for a in p.get("confirmed_attempts",[])+([p["finalized_attempt"]] if p.get("finalized_attempt") else []):
   if "429" in str(a.get("error")):any_429=True
   if a.get("is_null") is False:any_tx=True
 if any_tx:return "TRANSACTION_READBACK_AVAILABLE"
 if any_429:return "PUBLIC_RPC_RATE_LIMIT_INTERFERING"
 if any_status:return "SIGNATURE_VISIBLE_BUT_TRANSACTION_BODY_UNAVAILABLE"
 return "SIGNATURE_AND_TRANSACTION_READBACK_UNAVAILABLE"

def run(root,max_samples=2):
 rows,probes=asyncio.run(probe(root,max_samples))
 return {"revision":"USLS_106S","supersedes_diagnostic":"USLS_106R",
  "raw_record_count":len(rows),"probe_count":len(probes),"finding":classify(probes),
  "probes":probes,"certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_samples=2):
 d=run(root,max_samples)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_transaction_readback_availability_diagnostic.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
