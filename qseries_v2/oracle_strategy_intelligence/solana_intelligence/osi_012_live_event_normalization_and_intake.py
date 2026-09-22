from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime,timezone
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_006_high_frequency_opportunity_intake_runtime import intake

ALIASES={
 "new_pool":"NEW_POOL","pool_created":"NEW_POOL","liquidity_added":"LIQUIDITY_ADDED",
 "liquidity_removed":"LIQUIDITY_REMOVED","freeze_authority":"FREEZE_AUTHORITY",
 "mint_authority":"MINT_AUTHORITY","swap_acceleration":"SWAP_ACCELERATION",
 "wallet_cluster":"WALLET_CLUSTER","volume_burst":"VOLUME_BURST",
 "price_acceleration":"PRICE_ACCELERATION","rug_risk_change":"RUG_RISK_CHANGE",
}

def _read(path:Path):
 if path.suffix.lower()==".json":
  x=json.loads(path.read_text(encoding="utf-8",errors="replace"));return x if isinstance(x,list) else [x]
 out=[]
 for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
  try: out.append(json.loads(line))
  except Exception: pass
 return out

def _pick(d,*keys):
 for k in keys:
  if d.get(k) not in (None,""): return d[k]
 return None

def normalize(row:dict,source_path:str)->dict|None:
 asset=_pick(row,"asset_key","mint","token_mint","address","pool_mint")
 ts=_pick(row,"observed_at","timestamp","ts","created_at","block_time")
 typ=_pick(row,"event_type","type","kind","event")
 if not asset or not ts or not typ:return None
 typ=ALIASES.get(str(typ).lower(),str(typ).upper())
 if isinstance(ts,(int,float)):
  ts=datetime.fromtimestamp(float(ts),timezone.utc).isoformat()
 return {"asset_key":str(asset),"event_type":typ,"observed_at":str(ts),
         "source":"solana_native","source_record_id":str(_pick(row,"id","signature","tx_signature") or ""),
         "features":{"raw_source_path":source_path}}

def run(root:Path,now_iso:str)->dict:
 report=json.loads((root/"OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json").read_text(encoding="utf-8"))
 events=[]
 for src in report["live_sources"]:
  p=root/src["path"]
  for row in _read(p):
   if isinstance(row,dict):
    n=normalize(row,src["path"])
    if n: events.append(n)
 state=root/"runtime_state/solana_intelligence/osi_012_live_intake_state.json"
 result=intake(events,now_iso,state,300)
 result["normalized_event_count"]=len(events)
 return result
