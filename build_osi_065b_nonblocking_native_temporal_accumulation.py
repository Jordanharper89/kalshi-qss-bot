from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_065_short_horizon_temporal_accumulation.py"
TEST=ROOT/"test_osi_065b_nonblocking_native_temporal_accumulation.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time,hashlib
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import expand_live_solana_token_pools

def _record(asset,pair,raw):
 payload=getattr(raw,"payload",{}) or {}
 pools=payload.get("pools") or ()
 selected=next((p for p in pools if isinstance(p,dict) and str(p.get("pair_address"))==pair and p.get("price_usd") not in (None,"")),None)
 if selected is None:return None
 observed_at=str(getattr(raw,"observed_at",None) or "")
 source_id=str(getattr(raw,"source_id",None) or "")
 seed=f"{asset}|{pair}|{observed_at}|{selected.get('price_usd')}|{source_id}".encode("utf-8")
 oid="osi-live-"+hashlib.sha256(seed).hexdigest()
 return {
  "observation_id":oid,"source_id":source_id,
  "observation_type":str(getattr(raw,"observation_type",None) or "solana_token_pool_identity_liquidity"),
  "observed_at":observed_at,"sequence_number":None,
  "provider":str(getattr(raw,"provider",None) or ""),
  "subject":str(getattr(raw,"subject",None) or asset),
  "payload":{"token_address":asset,"pool_count":1,"pools":[selected]},
 }

def accumulate(root,cycles=15,sleep_seconds=5.0):
 anchor=json.loads((root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json").read_text(encoding="utf-8"))
 asset=str(anchor["asset_key"]);pair=str(anchor["pair_address"])
 anchor_pool={
  "pair_address":pair,"price_usd":anchor["price_usd"],
  "liquidity_usd":anchor.get("liquidity_usd"),"volume_h24":anchor.get("volume_h24"),
  "buys_h24":anchor.get("buys_h24"),"sells_h24":anchor.get("sells_h24"),
  "market_cap":anchor.get("market_cap"),"fdv":anchor.get("fdv"),
  "pair_created_at":anchor.get("pair_created_at"),"dex_id":anchor.get("dex_id"),
 }
 records=[{
  "observation_id":anchor["observation_id"],"source_id":anchor.get("source_id",""),
  "observation_type":"solana_token_pool_identity_liquidity",
  "observed_at":anchor["observed_at"],"sequence_number":None,"provider":"",
  "subject":asset,"payload":{"token_address":asset,"pool_count":1,"pools":[anchor_pool]},
 }]
 states=[]
 for i in range(1,cycles+1):
  raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
  rec=_record(asset,pair,raw)
  if rec is not None and rec["observation_id"] not in {x["observation_id"] for x in records}:
   records.append(rec)
  states.append({"cycle":i,"records":len(records),"observed_at":None if rec is None else rec["observed_at"],"price_usd":None if rec is None else rec["payload"]["pools"][0]["price_usd"]})
  if i<cycles:time.sleep(sleep_seconds)
 return {"revision":"OSI_065B","asset_key":asset,"pair_address":pair,"records":records,"record_count":len(records),"states":states,"execution_authority":False}

def write(root):
 d=accumulate(root)
 p=root/"runtime_state/solana_opportunities/outcomes/nonblocking_native_temporal_records.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_short_horizon_temporal_accumulation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"]);print("[PAIR]",d["pair_address"]);print("[RECORD_COUNT]",d["record_count"])
  for x in d["states"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  if d["record_count"]<2:self.fail("NONBLOCKING_TEMPORAL_HISTORY_DID_NOT_PROGRESS")
  print("[PASS] OSI-065B nonblocking native temporal accumulation")
  print("[TRADER] Captures real post-anchor pool prices without waiting on PostgreSQL ingestion")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" OSI-065B NONBLOCKING NATIVE TEMPORAL ACCUMULATION");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replaces PostgreSQL-blocking temporal accumulation with certified native acquisition callable")
if __name__=="__main__":main()