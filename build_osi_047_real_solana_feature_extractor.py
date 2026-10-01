from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_047_real_solana_feature_extractor.py"
TEST=ROOT/"test_osi_047_real_solana_feature_extractor.py"
MOD_TEXT=r"""from __future__ import annotations
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
"""
TEST_TEXT=r"""import unittest,collections,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_047_real_solana_feature_extractor import sample
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=sample(ROOT);self.assertGreater(d["row_count"],0)
  print("[ROWS]",d["row_count"]);print("[ROWS_WITH_FEATURES]",d["rows_with_features"])
  keys=collections.Counter(k for r in d["rows"] for k in r["features"]);print("[FEATURE_COUNTS]",json.dumps(dict(keys),sort_keys=True))
  if d["rows_with_features"]==0:self.fail("NO_REAL_SOLANA_FEATURES_EXTRACTED")
  print("[PASS] OSI-047 real Solana feature extractor")
  print("[TRADER] Converts actual scraped Solana/GMGN fields into formula-ready variables")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-047 REAL SOLANA FEATURE EXTRACTOR");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
