from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def _pair(record):
 payload=getattr(record,"payload",{}) or {}
 pools=payload.get("pools") or []
 for p in pools:
  if not isinstance(p,dict):continue
  pair=p.get("pair_address")
  price=p.get("price_usd")
  if pair:
   return str(pair),price
 return None,None

def audit(root):
 intake=root/"runtime_state/solana_opportunities/intake/normalized_events.jsonl"
 lines=intake.read_text(encoding="utf-8",errors="replace").splitlines()
 if not lines:raise RuntimeError("NO_LIVE_SOLANA_OPPORTUNITY")
 opp=json.loads(lines[-1]);asset=str(opp.get("asset_key") or "")
 records=tuple(read_pinned_pool_history(asset,root=root,limit=512))
 matches=[]
 for r in records:
  pair,price=_pair(r)
  if pair:
   matches.append({
    "observation_id":r.observation_id,
    "observed_at":r.observed_at,
    "source_id":r.source_id,
    "pair_address":pair,
    "price_usd":price,
   })
 return {
  "revision":"OSI_060B","asset_key":asset,
  "native_history_records":len(records),
  "matches":matches,"match_count":len(matches),
  "resolution_source":"NATIVE_PINNED_POOL_HISTORY",
  "execution_authority":False,"read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/live_token_pair_resolution.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
