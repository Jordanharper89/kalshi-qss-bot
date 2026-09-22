from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import read
ALIASES={
 "liquidity":("liquidity","liquidity_usd","liquidity_value","pool_liquidity"),
 "price":("price","price_usd","usd_price"),
 "volume":("volume","volume_24h","volume_usd","volume24h"),
 "market_cap":("market_cap","marketcap","market_cap_usd"),
 "holder_count":("holder_count","holders","holder_num"),
 "freeze_authority":("freeze_authority","freezeable","freeze_authority_enabled"),
 "mint_authority":("mint_authority","mintable","mint_authority_enabled"),
 "buy_count":("buy_count","buys","buy_tx_count"),
 "sell_count":("sell_count","sells","sell_tx_count"),
 "slot":("slot","finalized_slot"),
}
def _flat(v,out=None):
 out={} if out is None else out
 if isinstance(v,dict):
  for k,x in v.items():
   out.setdefault(str(k).lower(),x)
   if isinstance(x,(dict,list)):_flat(x,out)
 elif isinstance(v,list):
  for x in v[:20]:
   if isinstance(x,(dict,list)):_flat(x,out)
 return out
def extract(row):
 f=_flat(row.get("canonical_observation_json") or {});features={}
 for name,keys in ALIASES.items():
  for k in keys:
   if k in f and not isinstance(f[k],(dict,list)):
    features[name]=f[k];break
 return {"observation_id":row.get("observation_id"),"source_id":row.get("source_id"),"observation_type":row.get("observation_type"),"observed_at":row.get("observed_at"),"features":features}
def sample(root,limit=500):
 rows=read(root,limit)["rows"];out=[extract(x) for x in rows]
 return {"rows":out,"row_count":len(out),"rows_with_features":sum(bool(x["features"]) for x in out),"execution_authority":False,"read_only":True}
