from __future__ import annotations
import json,time,hashlib,re
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
 discover_live_solana_tokens,expand_live_solana_token_pools,
)

BASE58_RE=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,48}$")

def _extract_token(v):
 if isinstance(v,str):
  return v if BASE58_RE.match(v) else None
 if isinstance(v,dict):
  for k in ("token_address","address","mint","base_address"):
   x=v.get(k)
   if isinstance(x,str) and BASE58_RE.match(x):return x
 return None

def _valid_pools(raw):
 payload=getattr(raw,"payload",{}) or {}
 pools=payload.get("pools") or ()
 out=[]
 for p in pools:
  if not isinstance(p,dict):continue
  if not p.get("pair_address") or p.get("price_usd") in (None,""):continue
  out.append(p)
 return out

def _best_pool(pools):
 if not pools:return None
 return sorted(
  pools,
  key=lambda p:(
   0 if p.get("liquidity_usd") is not None else 1,
   -(float(p.get("liquidity_usd") or 0.0)),
   -(float(p.get("volume_h24") or 0.0)),
  )
 )[0]

def _record(asset,raw,pool):
 observed_at=str(getattr(raw,"observed_at",None) or "")
 source_id=str(getattr(raw,"source_id",None) or "")
 pair=str(pool["pair_address"]);price=str(pool["price_usd"])
 seed=f"{asset}|{pair}|{observed_at}|{price}|{source_id}".encode("utf-8")
 oid="osi-live-"+hashlib.sha256(seed).hexdigest()
 return {
  "observation_id":oid,
  "source_id":source_id,
  "observation_type":str(getattr(raw,"observation_type",None) or "solana_token_pool_identity_liquidity"),
  "observed_at":observed_at,
  "sequence_number":None,
  "provider":str(getattr(raw,"provider",None) or ""),
  "subject":str(getattr(raw,"subject",None) or asset),
  "payload":{"token_address":asset,"pool_count":1,"pools":[pool]},
 }

def _resolve_viable():
 discovered=discover_live_solana_tokens(timeout_seconds=20.0)
 payload=getattr(discovered,"payload",{}) or {}
 tokens=payload.get("tokens") or ()
 candidates=[]
 for item in tokens:
  t=_extract_token(item)
  if t and t not in candidates:candidates.append(t)

 viable=[]
 for token in candidates[:30]:
  try:
   raw=expand_live_solana_token_pools(token_address=token,timeout_seconds=20.0)
  except Exception:
   continue
  pools=_valid_pools(raw)
  if not pools:continue
  pool=_best_pool(pools)
  viable.append((token,raw,pool))

 if not viable:
  raise RuntimeError("NO_VIABLE_DISCOVERED_SOLANA_POOL")

 viable.sort(key=lambda x:(
  0 if x[2].get("liquidity_usd") is not None else 1,
  -(float(x[2].get("liquidity_usd") or 0.0)),
  -(float(x[2].get("volume_h24") or 0.0)),
 ))
 return viable[0],len(candidates),len(viable)

def accumulate(root,cycles=14,sleep_seconds=5.0):
 (asset,raw0,pool0),candidate_count,viable_count=_resolve_viable()
 anchor=_record(asset,raw0,pool0)
 pair=str(pool0["pair_address"])

 anchor_doc={
  "revision":"OSI_065F",
  "asset_key":asset,
  "observation_id":anchor["observation_id"],
  "observed_at":anchor["observed_at"],
  "source_id":anchor["source_id"],
  "pair_address":pair,
  "price_usd":pool0["price_usd"],
  "liquidity_usd":pool0.get("liquidity_usd"),
  "volume_h24":pool0.get("volume_h24"),
  "buys_h24":pool0.get("buys_h24"),
  "sells_h24":pool0.get("sells_h24"),
  "market_cap":pool0.get("market_cap"),
  "fdv":pool0.get("fdv"),
  "pair_created_at":pool0.get("pair_created_at"),
  "dex_id":pool0.get("dex_id"),
  "anchor_source":"VIABLE_DISCOVERY_ATOMIC_NATIVE_CAPTURE",
  "candidate_count":candidate_count,
  "viable_count":viable_count,
  "execution_authority":False,
 }
 ap=root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json"
 ap.parent.mkdir(parents=True,exist_ok=True)
 ap.write_text(json.dumps(anchor_doc,indent=2,sort_keys=True),encoding="utf-8")

 records=[anchor]
 states=[]
 for i in range(1,cycles+1):
  time.sleep(sleep_seconds)
  raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
  pool=next((p for p in _valid_pools(raw) if str(p.get("pair_address"))==pair),None)
  rec=None if pool is None else _record(asset,raw,pool)
  if rec is not None and rec["observation_id"] not in {x["observation_id"] for x in records}:
   records.append(rec)
  states.append({
   "cycle":i,
   "target_age_seconds":i*sleep_seconds,
   "records":len(records),
   "observed_at":None if rec is None else rec["observed_at"],
   "price_usd":None if rec is None else rec["payload"]["pools"][0]["price_usd"],
  })

 return {
  "revision":"OSI_065F",
  "asset_key":asset,
  "pair_address":pair,
  "candidate_count":candidate_count,
  "viable_count":viable_count,
  "anchor_observation_id":anchor["observation_id"],
  "anchor_at":anchor["observed_at"],
  "records":records,
  "record_count":len(records),
  "states":states,
  "execution_authority":False,
 }

def write(root):
 d=accumulate(root)
 p=root/"runtime_state/solana_opportunities/outcomes/nonblocking_native_temporal_records.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
