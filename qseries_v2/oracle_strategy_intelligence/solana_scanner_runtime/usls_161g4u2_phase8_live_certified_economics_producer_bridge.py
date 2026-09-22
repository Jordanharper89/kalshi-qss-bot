from __future__ import annotations
import ast,asyncio,importlib,inspect,json,time
from pathlib import Path

IDX="runtime_state/solana_opportunities/solana_scanner/phase8_universal_certified_economics_source_index.json"
SIG=("trade_signature","signature")
FAM=("family","venue","program_family","source_family")
MKT=("market_address","pool_address","pool","curve_address","curve","market_key")
PRICE=("effective_price","price","execution_price","price_usd","effective_output_per_input")
TIME=("observed_unix","trade_observed_unix","received_unix","scanner_observed_unix","block_time")

def _first(d,ks):
 if not isinstance(d,dict):return None
 for k in ks:
  if d.get(k) not in (None,""):return d.get(k)
 return None

def _rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ("rows","trades","events","normalized_rows","ready_rows"):
   if isinstance(x.get(k),list):return x[k]
 return []

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 last=None
 for delay in (0,1,2,4):
  if delay:time.sleep(delay)
  try:return _rpc(method,params,timeout)
  except Exception as e:last=e
 raise last

async def _capture():
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=12,max_rows=10000)

def _producer_candidates(root,artifact_rel):
 base=Path(artifact_rel).name.lower()
 out=[]
 for p in (Path(root)/"qseries_v2").rglob("*.py"):
  try:src=p.read_text(encoding="utf-8",errors="ignore")
  except Exception:continue
  low=src.lower()
  if base not in low and str(artifact_rel).replace("\\","/").lower() not in low:continue
  try:tree=ast.parse(src)
  except Exception:continue
  mod=str(p.relative_to(root))[:-3].replace("\\","/").replace("/",".")
  try:m=importlib.import_module(mod)
  except Exception:continue
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    fn=getattr(m,n.name,None)
    if not callable(fn):continue
    nm=n.name.lower()
    if any(w in nm for w in ("material","normal","decode","economic","trade","row","build","run")):
     try:sig=inspect.signature(fn)
     except Exception:continue
     out.append((mod,n.name,fn,list(sig.parameters)))
 return out

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _extract(obj,live_sig,fam):
 objs=[];_walk(obj,objs)
 for o in objs:
  sig=_first(o,SIG) or live_sig
  market=_first(o,MKT);price=_first(o,PRICE)
  if market is None or price is None:continue
  try:price=float(price)
  except Exception:continue
  return {"family":fam,"trade_signature":sig,"market_address":market,
   "effective_price":price,"observed_unix":_first(o,TIME) or time.time()}
 return None

def _invoke(fn,params,row,tx,sig,root):
 args=[]
 if len(params)==0:args=[()]
 elif len(params)==1:
  n=params[0].lower()
  if "root" in n or "path" in n:args=[(Path(root),)]
  elif "sig" in n:args=[(sig,)]
  elif "tx" in n or "transaction" in n:args=[(tx,)]
  else:args=[({**row,"transaction":tx,"signature":sig,"trade_signature":sig},)]
 elif len(params)==2:
  args=[(row,tx),(sig,tx),(Path(root),row),(Path(root),tx)]
 for a in args:
  try:
   got=fn(*a)
   if inspect.isawaitable(got):continue
   x=_extract(got,sig,str(_first(row,FAM) or "").upper())
   if x:return x
  except Exception:pass
 return None

def run(root):
 root=Path(root);idx=json.loads((root/IDX).read_text(encoding="utf-8"))
 ready=idx.get("certified_economics_ready_families") or []
 artifacts={}
 for fam in ready:
  arts=(idx.get("family_support",{}).get(fam,{}) or {}).get("artifacts") or []
  artifacts[fam]=arts
 producers={}
 for fam,arts in artifacts.items():
  ps=[]
  for a in arts:ps.extend(_producer_candidates(root,a))
  # de-dupe
  seen=set();uniq=[]
  for x in ps:
   k=(x[0],x[1],tuple(x[3]))
   if k not in seen:seen.add(k);uniq.append(x)
  producers[fam]=uniq
 live=_rows(asyncio.run(_capture()))
 chosen=[];seen_sig=set()
 for r in live:
  fam=str(_first(r,FAM) or "").upper();sig=_first(r,SIG)
  if fam in ready and sig and sig not in seen_sig:
   chosen.append(r);seen_sig.add(sig)
  if len(chosen)>=16:break
 out=[];attempts=0
 for r in chosen:
  fam=str(_first(r,FAM) or "").upper();sig=_first(r,SIG)
  try:tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except Exception:continue
  if not isinstance(tx,dict):continue
  for mod,name,fn,params in producers.get(fam,[]):
   attempts+=1
   x=_invoke(fn,params,r,tx,sig,root)
   if x:
    x["producer_module"]=mod;x["producer_function"]=name
    x["execution_authority"]=False;out.append(x);break
 by={}
 for x in out:
  z=by.setdefault(x["family"],{"rows":0,"markets":set()})
  z["rows"]+=1;z["markets"].add(str(x["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_161G4U2","ready_families":ready,
  "producer_candidate_counts":{f:len(v) for f,v in producers.items()},
  "live_target_signature_count":len(chosen),"producer_invoke_attempts":attempts,
  "live_certified_economic_row_count":len(out),"family_support":support,"rows":out,
  "next_boundary":("UNIVERSAL_PROSPECTIVE_SETUP_FREEZE" if out else
   "CERTIFIED_ARTIFACTS_ARE_HISTORICAL_ONLY_OR_PRODUCER_INTERFACE_NOT_REPLAYABLE"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_live_certified_producer_bridge.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
