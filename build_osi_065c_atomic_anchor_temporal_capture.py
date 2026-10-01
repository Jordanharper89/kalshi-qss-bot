from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_065_short_horizon_temporal_accumulation.py"
TEST=ROOT/"test_osi_065c_atomic_anchor_temporal_capture.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time,hashlib
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
 select_live_solana_token,expand_live_solana_token_pools,
)

def _choose(raw,pair=None):
 payload=getattr(raw,"payload",{}) or {}
 pools=payload.get("pools") or ()
 valid=[p for p in pools if isinstance(p,dict) and p.get("pair_address") and p.get("price_usd") not in (None,"")]
 if pair is not None:
  valid=[p for p in valid if str(p.get("pair_address"))==str(pair)]
 if not valid:return None
 valid.sort(key=lambda p:(-(float(p.get("liquidity_usd") or 0.0)),-(float(p.get("volume_h24") or 0.0))))
 return valid[0]

def _record(asset,raw,pool):
 observed_at=str(getattr(raw,"observed_at",None) or "")
 source_id=str(getattr(raw,"source_id",None) or "")
 pair=str(pool["pair_address"]);price=str(pool["price_usd"])
 seed=f"{asset}|{pair}|{observed_at}|{price}|{source_id}".encode("utf-8")
 oid="osi-live-"+hashlib.sha256(seed).hexdigest()
 return {
  "observation_id":oid,"source_id":source_id,
  "observation_type":str(getattr(raw,"observation_type",None) or "solana_token_pool_identity_liquidity"),
  "observed_at":observed_at,"sequence_number":None,
  "provider":str(getattr(raw,"provider",None) or ""),
  "subject":str(getattr(raw,"subject",None) or asset),
  "payload":{"token_address":asset,"pool_count":1,"pools":[pool]},
 }

def accumulate(root,cycles=14,sleep_seconds=5.0):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")

 raw0=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
 pool0=_choose(raw0)
 if pool0 is None:raise RuntimeError("NO_USABLE_POOL_FOR_ATOMIC_ANCHOR")
 anchor=_record(asset,raw0,pool0)
 pair=str(pool0["pair_address"])

 anchor_doc={
  "revision":"OSI_065C","asset_key":asset,"observation_id":anchor["observation_id"],
  "observed_at":anchor["observed_at"],"source_id":anchor["source_id"],
  "pair_address":pair,"price_usd":pool0["price_usd"],
  "liquidity_usd":pool0.get("liquidity_usd"),"volume_h24":pool0.get("volume_h24"),
  "buys_h24":pool0.get("buys_h24"),"sells_h24":pool0.get("sells_h24"),
  "market_cap":pool0.get("market_cap"),"fdv":pool0.get("fdv"),
  "pair_created_at":pool0.get("pair_created_at"),"dex_id":pool0.get("dex_id"),
  "anchor_source":"ATOMIC_LIVE_NATIVE_CAPTURE","execution_authority":False,
 }
 ap=root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json"
 ap.write_text(json.dumps(anchor_doc,indent=2,sort_keys=True),encoding="utf-8")

 records=[anchor];states=[]
 for i in range(1,cycles+1):
  time.sleep(sleep_seconds)
  raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
  pool=_choose(raw,pair)
  rec=None if pool is None else _record(asset,raw,pool)
  if rec is not None and rec["observation_id"] not in {x["observation_id"] for x in records}:records.append(rec)
  states.append({"cycle":i,"elapsed_target_seconds":i*sleep_seconds,"records":len(records),
   "observed_at":None if rec is None else rec["observed_at"],
   "price_usd":None if rec is None else rec["payload"]["pools"][0]["price_usd"]})

 return {"revision":"OSI_065C","asset_key":asset,"pair_address":pair,
  "anchor_observation_id":anchor["observation_id"],"anchor_at":anchor["observed_at"],
  "records":records,"record_count":len(records),"states":states,"execution_authority":False}

def write(root):
 d=accumulate(root)
 p=root/"runtime_state/solana_opportunities/outcomes/nonblocking_native_temporal_records.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from datetime import datetime
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_short_horizon_temporal_accumulation import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"]);print("[PAIR]",d["pair_address"])
  print("[ANCHOR_OBSERVATION]",d["anchor_observation_id"]);print("[ANCHOR_AT]",d["anchor_at"])
  print("[RECORD_COUNT]",d["record_count"])
  anchor=datetime.fromisoformat(d["anchor_at"].replace("Z","+00:00"))
  for r in d["records"][1:]:
   t=datetime.fromisoformat(r["observed_at"].replace("Z","+00:00"))
   print("[RECORD]",json.dumps({"age_seconds":round((t-anchor).total_seconds(),3),"observed_at":r["observed_at"],
    "price_usd":r["payload"]["pools"][0]["price_usd"]},sort_keys=True))
  if d["record_count"]<5:self.fail("ATOMIC_TEMPORAL_CAPTURE_INSUFFICIENT_RECORDS")
  print("[PASS] OSI-065C atomic anchor + temporal capture")
  print("[TRADER] Fresh anchor and 5-second follow-up prices are captured in one uninterrupted prospective run")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-065C ATOMIC PROSPECTIVE ANCHOR + TEMPORAL CAPTURE")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 (root_out:=ROOT/"runtime_state/solana_opportunities/outcomes").mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Repairs stale time-gap between prospective anchor and post-anchor temporal observations")

if __name__=="__main__":
 main()
