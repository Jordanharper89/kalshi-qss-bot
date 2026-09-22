from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161g4u3_phase8_strict_live_economics_provenance_gate.py"
TEST=ROOT/"test_usls_161g4u3_phase8_strict_live_economics_provenance_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,importlib,inspect,json,time
from pathlib import Path

PREV="runtime_state/solana_opportunities/solana_scanner/phase8_universal_live_certified_producer_bridge.json"
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
  for k in ("rows","events","notifications","captured","raw_rows"):
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

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _strict_extract(obj,live_sig,live_time):
 objs=[];_walk(obj,objs)
 for o in objs:
  sig=_first(o,SIG)
  if sig!=live_sig:continue
  market=_first(o,MKT);price=_first(o,PRICE);ts=_first(o,TIME)
  if market is None or price is None:continue
  try:price=float(price)
  except Exception:continue
  if ts is not None:
   try:
    if live_time is not None and float(ts)+2 < float(live_time):continue
   except Exception:continue
  return {"trade_signature":sig,"market_address":market,"effective_price":price,
          "observed_unix":float(ts) if ts is not None else float(live_time)}
 return None

def _candidate_from_previous(root):
 prev=json.loads((Path(root)/PREV).read_text(encoding="utf-8"))
 out={}
 for r in prev.get("rows",[]):
  fam=str(r.get("family") or "").upper()
  mod=r.get("producer_module");fn=r.get("producer_function")
  if fam and mod and fn:out.setdefault(fam,set()).add((mod,fn))
 return {f:sorted(v) for f,v in out.items()}

def _invoke(fn,row,tx,sig):
 params=list(inspect.signature(fn).parameters)
 if len(params)==1:
  n=params[0].lower()
  if "sig" in n:return fn(sig)
  if "tx" in n or "transaction" in n:return fn(tx)
  if any(w in n for w in ("row","event","record")):
   return fn({**row,"transaction":tx,"signature":sig,"trade_signature":sig})
 if len(params)==2:
  trials=((row,tx),(sig,tx))
  for a in trials:
   try:return fn(*a)
   except Exception:pass
 raise TypeError("NON_REPLAYABLE_SIGNATURE")

def run(root):
 root=Path(root);cands=_candidate_from_previous(root)
 live=_rows(asyncio.run(_capture()))
 chosen=[];seen=set()
 for r in live:
  fam=str(_first(r,FAM) or "").upper();sig=_first(r,SIG)
  if fam in cands and sig and sig not in seen:
   chosen.append(r);seen.add(sig)
  if len(chosen)>=16:break
 out=[];attempts=0;rejected=0
 for r in chosen:
  fam=str(_first(r,FAM) or "").upper();sig=_first(r,SIG)
  live_time=_first(r,TIME) or time.time()
  try:tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except Exception:continue
  if not isinstance(tx,dict):continue
  for modname,fnname in cands.get(fam,[]):
   try:
    fn=getattr(importlib.import_module(modname),fnname)
    params=list(inspect.signature(fn).parameters)
    if len(params)==0 or any(x.lower() in ("root","path") for x in params):
     rejected+=1;continue
    attempts+=1
    got=_invoke(fn,r,tx,sig)
    x=_strict_extract(got,sig,live_time)
    if x:
     out.append({"family":fam,**x,"producer_module":modname,
      "producer_function":fnname,"strict_live_provenance":True,
      "execution_authority":False})
     break
   except Exception:
    continue
 by={}
 for x in out:
  z=by.setdefault(x["family"],{"rows":0,"markets":set()})
  z["rows"]+=1;z["markets"].add(str(x["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_161G4U3","live_target_signature_count":len(chosen),
  "strict_invoke_attempts":attempts,"non_replayable_candidates_rejected":rejected,
  "strict_live_economic_row_count":len(out),"family_support":support,"rows":out,
  "strict_rule":"OUTPUT_MUST_EXPLICITLY_CONTAIN_SAME_LIVE_SIGNATURE_PLUS_MARKET_PLUS_PRICE",
  "next_boundary":("UNIVERSAL_PROSPECTIVE_SETUP_FREEZE_STRICT" if out else
   "REBUILD_LIVE_ECONOMICS_PRODUCER_BOUNDARY_NO_MORE_ADAPTERS"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_economics_provenance.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g4u3_phase8_strict_live_economics_provenance_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"live_target_signature_count":d["live_target_signature_count"],
   "strict_invoke_attempts":d["strict_invoke_attempts"],
   "non_replayable_candidates_rejected":d["non_replayable_candidates_rejected"],
   "strict_live_economic_row_count":d["strict_live_economic_row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["live_target_signature_count"],0,"NO_LIVE_TARGET_SIGNATURES")
  self.assertGreater(d["strict_live_economic_row_count"],0,
   "NO_STRICT_SIGNATURE_PROVEN_LIVE_ECONOMIC_ROWS")
  self.assertTrue(all(x["strict_live_provenance"] for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161G4U3 strict live economics provenance")
  print("[PASS] each accepted row explicitly contains the same fresh live signature + market + price")
  print("[NEXT] UNIVERSAL_PROSPECTIVE_SETUP_FREEZE_STRICT")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
