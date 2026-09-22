from __future__ import annotations
import asyncio,inspect,json,time,hashlib
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"
BIRTHS="runtime_state/solana_opportunities/solana_scanner/exact_births.jsonl"
TARGETS=("PUMP_FUN","METEORA_DBC","METEORA_DAMM")

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

def _notif(r):return r.get("raw_notification") or {}
def _sig(r):return r.get("signature") or _walk(_notif(r),"signature")
def _logs(r):
 n=_notif(r)
 for box in (n,n.get("value") if isinstance(n,dict) else None,
             (n.get("result") or {}).get("value") if isinstance(n.get("result"),dict) else None):
  if isinstance(box,dict):
   for k in ("logs","logMessages"):
    if isinstance(box.get(k),list):return box[k]
 return []

def _family(r):
 n=_notif(r)
 for k in ("family","venue","launcher_family","source_family"):
  v=_walk(n,k)
  if v not in (None,""):return str(v)
 return "UNKNOWN"

def _notif_err(r):
 n=_notif(r)
 v=n.get("value")
 if isinstance(v,dict) and "err" in v:return v.get("err")
 rr=n.get("result")
 if isinstance(rr,dict):
  vv=rr.get("value")
  if isinstance(vv,dict) and "err" in vv:return vv.get("err")
 if "err" in n:return n.get("err")
 return _walk(n,"err")

def _hint(r):
 fam=_family(r);low="\n".join(map(str,_logs(r))).lower()
 if fam=="PUMP_FUN":
  return "instruction: create" in low
 if fam in ("METEORA_DBC","METEORA_DAMM"):
  return ("instruction: initializepoolwithdynamicconfig" in low or
          "instruction: migrate" in low or "initializevirtualpool" in low)
 return False

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

def _fair_select(rows,max_total=18):
 by={f:[] for f in TARGETS}
 for r in rows:
  f=_family(r)
  if f in by:by[f].append(r)
 for f in TARGETS:
  by[f].sort(key=lambda r:(not _hint(r), str(_sig(r))))
 out=[];i=0
 while len(out)<max_total and any(i<len(by[f]) for f in TARGETS):
  for f in TARGETS:
   if i<len(by[f]) and len(out)<max_total:out.append(by[f][i])
  i+=1
 return out,by

async def _one(row,max_attempts=3):
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
    if hit:
     return attempts,{"record_id":_rid({"family":fam,"signature":sig,"semantic":semantic}),
      "family":fam,"signature":sig,"slot":tx.get("slot"),"block_time":tx.get("blockTime"),
      "observed_unix":row.get("scanner_observed_unix"),"semantic":semantic,
      "instructions":instructions,"raw_transaction":tx,"identity_materialized":False,
      "execution_authority":False}
    return attempts,None
  except Exception as e:
   attempts.append({"attempt":n,"state":"RPC_ERROR","error":repr(e)})
  if n<max_attempts:await asyncio.sleep(3.0*(2**(n-1)))
 return attempts,None

async def cycle(root,seconds=12,max_total=18):
 from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106p_scanner_raw_program_admission_before_classification import run as admit
 before=_read_jsonl(Path(root)/RAW);seen={x.get("record_id") for x in before}
 admission=await asyncio.to_thread(admit,root,seconds)
 fresh=[x for x in _read_jsonl(Path(root)/RAW) if x.get("record_id") not in seen]
 eligible=[r for r in fresh if _family(r) in TARGETS and _notif_err(r) is None and _sig(r)]
 selected,by=_fair_select(eligible,max_total)
 results=[];births=[]
 for i,row in enumerate(selected):
  attempts,birth=await _one(row)
  results.append({"family":_family(row),"signature":_sig(row),"birth_hint":_hint(row),
                  "attempts":attempts,"exact_birth":birth is not None})
  if birth:births.append(birth)
  if i+1<len(selected):await asyncio.sleep(1.25)
 return admission,fresh,eligible,by,results,births

def run(root,cycles=3,seconds=12,max_total=18):
 root=Path(root);history=[];all_births=[]
 for i in range(1,cycles+1):
  admission,fresh,eligible,by,results,births=asyncio.run(cycle(root,seconds,max_total))
  history.append({"cycle":i,"fresh_raw_rows":len(fresh),
   "eligible_successful_target_rows":len(eligible),
   "family_eligible_counts":{k:len(v) for k,v in by.items()},
   "family_hint_counts":{k:sum(_hint(x) for x in v) for k,v in by.items()},
   "dispatch_attempted":len(results),
   "family_dispatch_counts":{k:sum(x["family"]==k for x in results) for k in TARGETS},
   "exact_births":len(births),"results":results})
  all_births.extend(births)
  if births:break
 bp=root/BIRTHS;bp.parent.mkdir(parents=True,exist_ok=True)
 old=_read_jsonl(bp);seen={x.get("record_id") for x in old}
 new=[b for b in all_births if b["record_id"] not in seen]
 if new:
  with bp.open("a",encoding="utf-8") as f:
   for b in new:f.write(_canon(b)+"\n")
 return {"revision":"USLS_106ZA","cycles_completed":len(history),"history":history,
  "exact_births_detected":len(all_births),"exact_births_persisted_new":len(new),
  "total_exact_birth_records":len(_read_jsonl(bp)),
  "birth_hint_is_priority_only":True,"fair_family_dispatch":True,
  "state":"EXACT_BIRTH_CAPTURED_IDENTITY_NEXT" if all_births else "WAITING_FOR_EXACT_PROSPECTIVE_BIRTH",
  "identity_materialization_certified":False,"lifecycle_join_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,cycles=3,seconds=12,max_total=18):
 d=run(root,cycles,seconds,max_total)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_birth_priority_fair_dispatch_loop.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
