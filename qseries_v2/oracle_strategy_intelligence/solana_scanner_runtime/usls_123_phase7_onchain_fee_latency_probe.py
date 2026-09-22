from __future__ import annotations
import json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={}
 for x in d.get("rows",[]):
  fam=x.get("family");sig=x.get("trade_signature")
  if fam and sig and fam not in chosen:chosen[fam]=x
 rows=[]
 for i,(fam,x) in enumerate(sorted(chosen.items())):
  sig=x["trade_signature"];tx=None;err=None
  try:
   tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except Exception as e:err=repr(e)
  meta=(tx or {}).get("meta") or {}
  block=(tx or {}).get("blockTime")
  obs=x.get("trade_observed_unix")
  latency=None
  if isinstance(obs,(int,float)) and isinstance(block,(int,float)):
   latency=max(0.0,float(obs)-float(block))
  rows.append({"family":fam,"trade_signature":sig,
   "tx_found":isinstance(tx,dict),"rpc_error":err,
   "network_fee_lamports":meta.get("fee"),
   "block_time":block,"observed_unix":obs,
   "observation_latency_seconds":latency,
   "compute_units_consumed":meta.get("computeUnitsConsumed"),
   "execution_authority":False})
  if i+1<len(chosen):time.sleep(0.8)
 by={x["family"]:x for x in rows}
 return {"revision":"USLS_123","family_probe_count":len(rows),
  "tx_found_count":sum(x["tx_found"] for x in rows),
  "fee_found_count":sum(x["network_fee_lamports"] is not None for x in rows),
  "latency_found_count":sum(x["observation_latency_seconds"] is not None for x in rows),
  "rows":rows,"families":by,
  "fee_semantics":"SOLANA_NETWORK_FEE_LAMPORTS_NOT_QUOTE_DENOMINATED_FEE_FRACTION",
  "next_boundary":"SOURCE_NATIVE_LIQUIDITY_AND_FEE_EVIDENCE_EXTRACTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_onchain_fee_latency_probe.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
