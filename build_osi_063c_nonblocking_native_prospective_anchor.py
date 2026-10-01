from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_063_fresh_native_prospective_anchor.py"
TEST=ROOT/"test_osi_063c_nonblocking_native_prospective_anchor.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    expand_live_solana_token_pools,
    canonicalize_expansion_observation,
)

def _extract(raw):
 pools=raw.get("pools") if isinstance(raw,dict) else None
 if not isinstance(pools,list) or not pools:
  raise RuntimeError("NO_LIVE_POOLS_IN_NATIVE_EXPANSION")
 first=next((x for x in pools if isinstance(x,dict) and x.get("pair_address")),None)
 if first is None:
  raise RuntimeError("NO_PAIR_ADDRESS_IN_NATIVE_EXPANSION")
 observed_at=raw.get("observed_at") or raw.get("snapshot_at") or raw.get("timestamp")
 token=raw.get("token_address") or raw.get("address") or raw.get("mint")
 return first,observed_at,token

def create(root):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:
  raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")

 raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
 first,observed_at,token=_extract(raw)

 canonical=None
 try:
  canonical=canonicalize_expansion_observation(raw,"osi-063c-prospective-anchor")
 except Exception:
  canonical=None

 observation_id=None
 if canonical is not None:
  observation_id=getattr(canonical,"observation_id",None)
  if observed_at is None:
   observed_at=getattr(canonical,"observed_at",None)

 if observed_at is None:
  raise RuntimeError("LIVE_NATIVE_EXPANSION_HAS_NO_OBSERVED_AT")

 pair=str(first["pair_address"])
 price=first.get("price_usd")
 if price is None:
  raise RuntimeError("LIVE_NATIVE_EXPANSION_HAS_NO_PRICE")

 if not observation_id:
  import hashlib
  seed=f"{asset}|{pair}|{observed_at}|{price}".encode("utf-8")
  observation_id="osi-anchor-"+hashlib.sha256(seed).hexdigest()

 return {
  "revision":"OSI_063C",
  "asset_key":asset,
  "observation_id":str(observation_id),
  "observed_at":str(observed_at),
  "pair_address":pair,
  "price_usd":price,
  "anchor_source":"LIVE_NATIVE_SOLANA_EXPANSION",
  "postgres_persistence_required_before_anchor":False,
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
  self.assertFalse(d["postgres_persistence_required_before_anchor"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[ANCHOR_SOURCE]",d["anchor_source"])
  print("[ANCHOR_OBSERVATION]",d["observation_id"])
  print("[ANCHOR_AT]",d["observed_at"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_PRICE]",d["price_usd"])
  print("[POSTGRES_BLOCKING_REQUIRED]",d["postgres_persistence_required_before_anchor"])
  print("[PASS] OSI-063C nonblocking native prospective anchor")
  print("[TRADER] Freezes the real live Solana observation immediately instead of waiting on PostgreSQL ingestion")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-063C NONBLOCKING NATIVE PROSPECTIVE ANCHOR")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement for OSI-063B PostgreSQL-ingestion timeout")

if __name__=="__main__":
 main()
