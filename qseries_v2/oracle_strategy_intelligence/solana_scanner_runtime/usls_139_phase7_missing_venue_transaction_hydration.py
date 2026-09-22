from __future__ import annotations
import json,time
from pathlib import Path

MISSING=("PUMP_FUN","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")
SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={}
 for x in d.get("rows",[]):
  f=x.get("family");sig=x.get("trade_signature")
  if f in MISSING and sig and f not in chosen:chosen[f]=x
 rows=[]
 for i,f in enumerate(MISSING):
  x=chosen.get(f);tx=None;err=None
  if x:
   try:
    tx=_rpc("getTransaction",[x["trade_signature"],{"commitment":"confirmed",
      "encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
   except Exception as e:err=repr(e)
  meta=(tx or {}).get("meta") or {}
  rows.append({"family":f,"trade_signature":None if x is None else x.get("trade_signature"),
   "market_address":None if x is None else x.get("market_address"),
   "tx_found":isinstance(tx,dict),"rpc_error":err,
   "slot":None if tx is None else tx.get("slot"),
   "block_time":None if tx is None else tx.get("blockTime"),
   "network_fee_lamports":meta.get("fee"),
   "pre_token_balances":meta.get("preTokenBalances") or [],
   "post_token_balances":meta.get("postTokenBalances") or [],
   "pre_balances":meta.get("preBalances") or [],
   "post_balances":meta.get("postBalances") or [],
   "transaction":tx,"execution_authority":False})
  if i+1<len(MISSING):time.sleep(0.7)
 return {"revision":"USLS_139","family_count":len(rows),
  "tx_found_count":sum(x["tx_found"] for x in rows),
  "fee_found_count":sum(x["network_fee_lamports"] is not None for x in rows),
  "rows":rows,"next_boundary":"POOL_VAULT_PRE_POST_STATE_RECONSTRUCTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_missing_venue_transaction_hydration.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
