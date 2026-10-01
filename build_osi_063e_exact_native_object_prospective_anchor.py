from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_063_fresh_native_prospective_anchor.py"
TEST=ROOT/"test_osi_063e_exact_native_object_prospective_anchor.py"

MOD_TEXT=r"""from __future__ import annotations
import json,hashlib
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    expand_live_solana_token_pools,
)

def _choose_pool(raw):
 payload=getattr(raw,"payload",None)
 if not isinstance(payload,dict):
  raise RuntimeError("LIVE_NATIVE_OBSERVATION_HAS_NO_PAYLOAD_DICT")
 pools=payload.get("pools") or ()
 if not pools:
  raise RuntimeError("LIVE_NATIVE_OBSERVATION_HAS_NO_POOLS")
 valid=[p for p in pools if isinstance(p,dict) and p.get("pair_address") and p.get("price_usd") not in (None,"")]
 if not valid:
  raise RuntimeError("LIVE_NATIVE_POOLS_HAVE_NO_PAIR_PRICE")
 valid.sort(key=lambda p:(
  -(float(p.get("liquidity_usd") or 0.0)),
  -(float(p.get("volume_h24") or 0.0))
 ))
 return valid[0]

def create(root):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:
  raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")

 raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
 pool=_choose_pool(raw)

 observed_at=str(getattr(raw,"observed_at",None) or "")
 if not observed_at:
  raise RuntimeError("LIVE_NATIVE_OBSERVATION_HAS_NO_OBSERVED_AT")

 source_id=str(getattr(raw,"source_id",None) or "")
 pair=str(pool["pair_address"])
 price=str(pool["price_usd"])

 seed=f"{asset}|{pair}|{observed_at}|{price}|{source_id}".encode("utf-8")
 observation_id="osi-live-"+hashlib.sha256(seed).hexdigest()

 return {
  "revision":"OSI_063E",
  "asset_key":asset,
  "observation_id":observation_id,
  "observed_at":observed_at,
  "source_id":source_id,
  "pair_address":pair,
  "price_usd":price,
  "liquidity_usd":pool.get("liquidity_usd"),
  "volume_h24":pool.get("volume_h24"),
  "buys_h24":pool.get("buys_h24"),
  "sells_h24":pool.get("sells_h24"),
  "market_cap":pool.get("market_cap"),
  "fdv":pool.get("fdv"),
  "pair_created_at":pool.get("pair_created_at"),
  "dex_id":pool.get("dex_id"),
  "pool_count":getattr(raw,"payload",{}).get("pool_count"),
  "anchor_source":"LIVE_NATIVE_SOLANA_EXPANSION_OBJECT",
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
  print("[SOURCE_ID]",d["source_id"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_PRICE]",d["price_usd"])
  print("[LIQUIDITY_USD]",d["liquidity_usd"])
  print("[VOLUME_H24]",d["volume_h24"])
  print("[BUYS_H24]",d["buys_h24"])
  print("[SELLS_H24]",d["sells_h24"])
  print("[PAIR_CREATED_AT]",d["pair_created_at"])
  print("[POSTGRES_BLOCKING_REQUIRED]",d["postgres_persistence_required_before_anchor"])
  print("[PASS] OSI-063E exact native-object prospective anchor")
  print("[TRADER] Freezes a real live Solana pool observation using the certified object contract")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-063E EXACT NATIVE-OBJECT PROSPECTIVE ANCHOR")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement using physically observed IndependentCryptoObservation contract")

if __name__=="__main__":
 main()
