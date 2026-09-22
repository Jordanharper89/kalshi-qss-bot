from __future__ import annotations
import json
from pathlib import Path

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 lat=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_per_row_latency_recovery.json")
 dev=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_pretrade_reference_execution_deviation.json")
 fr=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_native_friction.json")
 lidx={x["trade_signature"]:x for x in lat.get("rows",[])}
 didx={x["trade_signature"]:x for x in dev.get("rows",[])}
 rows=[];fam={}
 for x in fr.get("rows",[]):
  sig=x["trade_signature"];l=lidx.get(sig,{});d=didx.get(sig,{})
  latency=l.get("observation_latency_seconds")
  ref=d.get("pre_trade_reference_price")
  deviation=d.get("realized_execution_deviation_fraction")
  have_fee=x.get("fee_supported",False);have_liq=x.get("liquidity_supported",False)
  ready=all((x.get("effective_price") is not None,latency is not None,ref is not None,
             deviation is not None,have_fee,have_liq))
  missing=[]
  if latency is None:missing.append("LATENCY")
  if ref is None or deviation is None:missing.append("PRETRADE_REFERENCE")
  if not have_fee:missing.append("FEE")
  if not have_liq:missing.append("LIQUIDITY")
  rows.append({"family":x["family"],"market_address":x.get("market_address"),
   "trade_signature":sig,"effective_price":x.get("effective_price"),
   "observation_latency_seconds":latency,"pre_trade_reference_price":ref,
   "realized_execution_deviation_fraction":deviation,
   "fee_evidence":x.get("fee_evidence"),"liquidity_evidence":x.get("liquidity_evidence"),
   "executable_candidate_ready":ready,"missing":missing,"execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"ready":0})
  z["rows"]+=1;z["ready"]+=ready
 return {"revision":"USLS_135","row_count":len(rows),
  "ready_count":sum(x["executable_candidate_ready"] for x in rows),
  "family_readiness":fam,"rows":rows,
  "readiness_semantics":"PHYSICAL_INPUT_COMPLETE_BUT_NATIVE_FEE_ASSET_MAY_STILL_REQUIRE_QUOTE_NORMALIZATION",
  "next_boundary":"PROSPECTIVE_EXECUTABLE_FREEZE_AND_LINEAGE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_executable_candidates.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
