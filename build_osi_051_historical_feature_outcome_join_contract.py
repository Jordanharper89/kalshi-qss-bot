from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_051_historical_feature_outcome_join_contract.py"
TEST=ROOT/"test_osi_051_historical_feature_outcome_join_contract.py"
MOD_TEXT=r"""from __future__ import annotations
def join(features:list[dict],outcomes:list[dict])->dict:
 by_id={str(x.get("observation_id") or x.get("case_id") or x.get("asset_key")):x for x in outcomes}
 rows=[]
 for f in features:
  key=str(f.get("observation_id") or f.get("case_id") or f.get("asset_key"))
  o=by_id.get(key)
  if not o:continue
  rows.append({"case_id":key,"observed_at":f.get("observed_at"),"features":f.get("features",{}),"outcomes":o.get("outcomes",o)})
 return {"revision":"OSI_051","cases":rows,"case_count":len(rows),"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_051_historical_feature_outcome_join_contract import join
class T(unittest.TestCase):
 def test_join(self):
  f=[{"observation_id":"a","observed_at":"2026-09-01T00:00:00+00:00","features":{"liquidity":1}}]
  o=[{"observation_id":"a","outcomes":{"60":.1}}]
  d=join(f,o);self.assertEqual(d["case_count"],1);self.assertEqual(d["cases"][0]["outcomes"]["60"],.1)
  print("[PASS] OSI-051 historical feature/outcome join contract")
  print("[TRADER] Locks the exact case shape scientific formula discovery will consume")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-051 HISTORICAL FEATURE / OUTCOME JOIN CONTRACT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()