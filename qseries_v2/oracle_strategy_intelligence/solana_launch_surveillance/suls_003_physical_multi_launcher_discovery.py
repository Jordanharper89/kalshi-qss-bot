from __future__ import annotations
import json,re
from pathlib import Path
from dataclasses import asdict
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import discover_live_solana_tokens,expand_live_solana_token_pools
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_001_universal_launcher_registry import classify
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_002_pool_birth_event_contract import SolanaPoolBirthEvent,verify

B58=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,48}$")
def _tok(x):
 if isinstance(x,dict):
  v=x.get("token_address")
  return v if isinstance(v,str) and B58.match(v) else None
 return None
def _num(v):
 try:return None if v is None else float(v)
 except Exception:return None

def acquire(limit=30):
 d=discover_live_solana_tokens(timeout_seconds=20.0);payload=getattr(d,"payload",{}) or {}
 tokens=[];events=[];failures=[]
 for x in payload.get("tokens") or ():
  t=_tok(x)
  if t and t not in tokens:tokens.append(t)
 for token in tokens[:limit]:
  try:r=expand_live_solana_token_pools(token_address=token,timeout_seconds=20.0)
  except Exception as e:
   failures.append({"token_address":token,"error":f"{type(e).__name__}: {e}"});continue
  p=getattr(r,"payload",{}) or {}
  for pool in p.get("pools") or ():
   if not isinstance(pool,dict) or not pool.get("pair_address"):continue
   ev=SolanaPoolBirthEvent(token,str(pool["pair_address"]),classify(pool.get("dex_id")),
    None if pool.get("dex_id") is None else str(pool.get("dex_id")),
    None if pool.get("pair_created_at") is None else int(pool.get("pair_created_at")),
    str(getattr(r,"observed_at","")), _num(pool.get("price_usd")),_num(pool.get("market_cap")),
    _num(pool.get("fdv")),_num(pool.get("liquidity_usd")),_num(pool.get("volume_h24")),
    None if pool.get("buys_h24") is None else int(pool.get("buys_h24")),
    None if pool.get("sells_h24") is None else int(pool.get("sells_h24")),
    str(getattr(r,"source_id","")),str(getattr(r,"provider","") or ""),
    str(getattr(r,"observation_type","") or ""),False)
   if verify(ev):events.append(asdict(ev))
 fam={}
 for e in events:fam[e["launcher_family"]]=fam.get(e["launcher_family"],0)+1
 return {"revision":"SULS_003","candidate_tokens":len(tokens),"event_count":len(events),
  "family_counts":fam,"events":events,"failures":failures,"execution_authority":False}

def write(root):
 d=acquire();p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_multi_launcher_discovery.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
