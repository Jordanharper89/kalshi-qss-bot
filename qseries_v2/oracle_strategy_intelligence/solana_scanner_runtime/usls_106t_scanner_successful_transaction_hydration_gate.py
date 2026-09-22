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

def _family(row):
 n=row.get("raw_notification") or {}
 for k in ("family","venue","launcher_family","source_family"):
  x=_walk(n,k)
  if x:return str(x)
 return "UNKNOWN"

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def _tx(sig):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return await _maybe(_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
  "maxSupportedTransactionVersion":1}],20.0))

async def probe(root,max_samples=12):
 rows=_rows(root);seen=set();cands=[]
 for r in reversed(rows):
  s=_sig(r)
  if s and s not in seen:
   seen.add(s);cands.append((r,str(s),_family(r)))
  if len(cands)>=max_samples:break
 out=[];successful=[]
 for i,(r,s,fam) in enumerate(cands):
  rec={"signature":s,"family":fam,"error":None,"tx_found":False,"meta_err":None,"slot":None}
  try:
   tx=await _tx(s)
   rec["tx_found"]=isinstance(tx,dict)
   if isinstance(tx,dict):
    rec["slot"]=tx.get("slot");rec["meta_err"]=(tx.get("meta") or {}).get("err")
    if rec["meta_err"] is None:
     successful.append({"signature":s,"family":fam,"transaction":tx})
  except Exception as e:
   rec["error"]=repr(e)
  out.append(rec)
  if successful:break
  if i+1<len(cands):await asyncio.sleep(1.5)
 return rows,out,successful

def run(root,max_samples=12):
 rows,probes,successful=asyncio.run(probe(root,max_samples))
 failed=sum(x["tx_found"] and x["meta_err"] is not None for x in probes)
 rate_limited=sum("429" in str(x["error"]) for x in probes)
 return {"revision":"USLS_106T","source_revision":"USLS_106S",
  "raw_record_count":len(rows),"probed_count":len(probes),
  "successful_transaction_count":len(successful),"failed_transaction_count":failed,
  "rate_limited_count":rate_limited,"probes":probes,
  "successful_transactions":successful,
  "finding":"SUCCESSFUL_TRANSACTION_HYDRATION_PROVEN" if successful else "NO_SUCCESSFUL_TX_IN_BOUNDED_SAMPLE",
  "failed_tx_policy":"RETAIN_RAW_ACTIVITY_BUT_EXCLUDE_FROM_EXACT_BIRTH_CERTIFICATION",
  "next_boundary":"EXACT_BIRTH_DECODING_FROM_SUCCESSFUL_HYDRATED_RAW_ACTIVITY",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_samples=12):
 d=run(root,max_samples)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_successful_transaction_hydration_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
