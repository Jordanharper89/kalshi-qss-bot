from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_036_comparable_case_feature_matrix.py"
TEST=ROOT/"test_osi_036_comparable_case_feature_matrix.py"
MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path

FEATURES=("liquidity","buy_sell_imbalance","swap_velocity","wallet_concentration","smart_money_flow",
          "holder_concentration","freeze_authority","mint_authority","pool_depth","volume_acceleration",
          "price_acceleration","sol_regime")

def _ts(v):
 if isinstance(v,(int,float)):return float(v)
 s=str(v).replace("Z","+00:00")
 return datetime.fromisoformat(s).timestamp()

def build(current:dict,history:list[dict])->dict:
 cutoff=_ts(current["observed_at"]);cases=[]
 for row in history:
  observed=row.get("observed_at")
  if observed is None:continue
  try:t=_ts(observed)
  except Exception:continue
  if t>=cutoff:continue
  feats={k:row.get(k) for k in FEATURES if k in row}
  cases.append({"case_id":row.get("case_id") or hashlib.sha256(json.dumps(row,sort_keys=True,default=str).encode()).hexdigest(),
                "observed_at":observed,"features":feats,"outcomes":row.get("outcomes",{})})
 return {"revision":"OSI_036","current_observed_at":current["observed_at"],"feature_names":list(FEATURES),
         "comparable_cases":cases,"case_count":len(cases),"future_data_excluded":True,
         "execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_036_comparable_case_feature_matrix import build
class T(unittest.TestCase):
 def test_future_exclusion(self):
  cur={"observed_at":"2026-09-18T18:00:00+00:00"}
  hist=[{"case_id":"past","observed_at":"2026-09-18T17:00:00+00:00","liquidity":1,"outcomes":{"60":.1}},
        {"case_id":"future","observed_at":"2026-09-18T19:00:00+00:00","liquidity":2,"outcomes":{"60":.2}}]
  d=build(cur,hist);self.assertEqual(d["case_count"],1);self.assertEqual(d["comparable_cases"][0]["case_id"],"past")
  self.assertTrue(d["future_data_excluded"]);self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-036 comparable-case feature matrix")
  print("[TRADER] Historical comparisons are frozen strictly before the live opportunity timestamp")
  print("[PASS] future_data_excluded=TRUE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-036 COMPARABLE-CASE FEATURE MATRIX");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
