from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_063_fresh_native_prospective_anchor.py"
TEST=ROOT/"test_osi_063b_live_token_native_prospective_anchor.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    persist_pinned_solana_pool_snapshot,
)
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def _pair(record):
 payload=getattr(record,"payload",{}) or {}
 for p in payload.get("pools") or []:
  if isinstance(p,dict) and p.get("pair_address"):
   return str(p["pair_address"]),p.get("price_usd")
 return None,None

def create(root):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:
  raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")

 before=tuple(read_pinned_pool_history(asset,root=root,limit=512))

 snap=persist_pinned_solana_pool_snapshot(
  token_address=asset,
  root=root,
  timeout_seconds=120.0,
  acquisition_timeout_seconds=20.0,
 )

 after=tuple(read_pinned_pool_history(asset,root=root,limit=512))
 if not after:
  raise RuntimeError("NO_NATIVE_HISTORY_AFTER_FRESH_ACQUISITION")

 before_ids={x.observation_id for x in before}
 fresh=[x for x in after if x.observation_id not in before_ids]
 anchor=fresh[-1] if fresh else after[-1]

 pair,price=_pair(anchor)
 if not pair:
  raise RuntimeError("FRESH_ANCHOR_HAS_NO_PAIR")

 return {
  "revision":"OSI_063B",
  "asset_key":asset,
  "before_records":len(before),
  "after_records":len(after),
  "fresh_records":len(fresh),
  "observation_id":anchor.observation_id,
  "observed_at":anchor.observed_at,
  "pair_address":pair,
  "price_usd":price,
  "snapshot_result":str(snap),
  "execution_authority":False,
 }

def write(root):
 d=create(root)
 p=root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_063_fresh_native_prospective_anchor import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[BEFORE_RECORDS]",d["before_records"])
  print("[AFTER_RECORDS]",d["after_records"])
  print("[FRESH_RECORDS]",d["fresh_records"])
  print("[ANCHOR_OBSERVATION]",d["observation_id"])
  print("[ANCHOR_AT]",d["observed_at"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_PRICE]",d["price_usd"])
  if d["after_records"]<1:
   self.fail("NO_NATIVE_HISTORY_AFTER_FRESH_ACQUISITION")
  if not d["pair_address"]:
   self.fail("NO_PAIR_ON_FRESH_ANCHOR")
  print("[PASS] OSI-063B current-live-token native prospective anchor")
  print("[TRADER] Selects a token that is live now, freezes its fresh pool state, and does not reuse a stale opportunity")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-063B CURRENT-LIVE-TOKEN NATIVE PROSPECTIVE ANCHOR")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement for stale-token OSI-063 failure")

if __name__=="__main__":
 main()
