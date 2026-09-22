from __future__ import annotations
import asyncio,json,time
from pathlib import Path

INDEX="runtime_state/solana_opportunities/solana_scanner/phase8_universal_certified_economics_source_index.json"
SIG=("trade_signature","signature")
MKT=("market_address","pool_address","pool","curve_address","curve","market_key")
PRICE=("effective_price","price","execution_price","price_usd","effective_output_per_input")
TIME=("observed_unix","trade_observed_unix","received_unix","scanner_observed_unix","block_time")
FAM=("family","venue","program_family","source_family")

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

def _read_rows(p):
 try:
  if p.suffix==".json":return _rows(json.loads(p.read_text(encoding="utf-8",errors="ignore")))
  if p.suffix==".jsonl":
   out=[]
   for ln in p.read_text(encoding="utf-8",errors="ignore").splitlines():
    try:
     x=json.loads(ln)
     if isinstance(x,dict):out.append(x)
    except Exception:pass
   return out
 except Exception:return []
 return []

async def _capture(seconds,max_rows):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=seconds,max_rows=max_rows)

def run(root,seconds=15,max_rows=12000):
 root=Path(root);idx=json.loads((root/INDEX).read_text(encoding="utf-8"))
 live=_rows(asyncio.run(_capture(seconds,max_rows)))
 wanted={}
 for r in live:
  sig=_first(r,SIG);fam=str(_first(r,FAM) or "").upper()
  if sig:wanted[sig]={"family":fam,"live_observed_unix":_first(r,TIME)}
 artifacts=set()
 for v in idx["family_support"].values():artifacts.update(v.get("artifacts") or [])
 # Allow existing writers a moment to flush before readback.
 time.sleep(2)
 joined=[]
 for rel in sorted(artifacts):
  p=root/rel
  if not p.exists():continue
  for r in _read_rows(p):
   sig=_first(r,SIG)
   if sig not in wanted:continue
   market=_first(r,MKT);price=_first(r,PRICE);ts=_first(r,TIME)
   if market is None or price is None:continue
   try:price=float(price)
   except Exception:continue
   fam=str(_first(r,FAM) or wanted[sig]["family"] or "").upper()
   joined.append({"family":fam,"trade_signature":sig,"market_address":market,
    "effective_price":price,"observed_unix":ts or wanted[sig]["live_observed_unix"] or time.time(),
    "source_artifact":rel,"execution_authority":False})
 by={}
 for x in joined:
  z=by.setdefault(x["family"],{"rows":0,"markets":set()});z["rows"]+=1;z["markets"].add(str(x["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_161G4U","live_row_count":len(live),"live_signature_count":len(wanted),
  "joined_economic_row_count":len(joined),"family_support":support,"rows":joined,
  "next_boundary":"UNIVERSAL_PROSPECTIVE_SETUP_FREEZE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_live_economics_bridge.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
