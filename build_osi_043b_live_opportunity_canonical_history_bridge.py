from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_043_live_opportunity_to_historical_formula_bridge.py"
TEST=ROOT/"test_osi_043b_live_opportunity_canonical_history_bridge.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_042_bounded_solana_postgresql_sample_reader import read
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_036_comparable_case_feature_matrix import build
FEATURES=("liquidity","buy_sell_imbalance","swap_velocity","wallet_concentration","smart_money_flow","holder_concentration","freeze_authority","mint_authority","pool_depth","volume_acceleration","price_acceleration","sol_regime")
def _flat(v,out=None):
 out={} if out is None else out
 if isinstance(v,dict):
  for k,x in v.items():
   if isinstance(x,(dict,list)):_flat(x,out)
   elif k not in out:out[str(k).lower()]=x
 elif isinstance(v,list):
  for x in v[:25]:_flat(x,out)
 return out
def _history(rows:list[dict])->list[dict]:
 out=[]
 for i,r in enumerate(rows):
  payload=r.get("canonical_observation_json") or {};f=_flat(payload)
  feats={k:f.get(k) for k in FEATURES if k in f}
  outcomes=f.get("outcomes") if isinstance(f.get("outcomes"),dict) else {}
  out.append({"case_id":f.get("observation_id") or f.get("signature") or f"pg-{i}","observed_at":r.get("observed_at"),**feats,"outcomes":outcomes,"source_id":r.get("source_id")})
 return out
def bridge(root:Path)->dict:
 intake=root/"runtime_state/solana_opportunities/intake/normalized_events.jsonl"
 lines=intake.read_text(encoding="utf-8",errors="replace").splitlines()
 if not lines:raise RuntimeError("No live opportunity events")
 opp=json.loads(lines[-1]);hist=read(root,250);cases=_history(hist["rows"])
 matrix=build({"observed_at":opp["observed_at"],"asset_key":opp["asset_key"]},cases)
 return {"revision":"OSI_043B","asset_key":opp["asset_key"],"source_table":hist["table"],"historical_rows":hist["row_count"],"comparable_case_count":matrix["case_count"],"future_data_excluded":matrix["future_data_excluded"],"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_043_live_opportunity_to_historical_formula_bridge import bridge
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=bridge(ROOT);self.assertFalse(d["execution_authority"]);self.assertTrue(d["future_data_excluded"])
  print("[ASSET]",d["asset_key"]);print("[SOURCE_TABLE]",d["source_table"]);print("[HISTORICAL_ROWS]",d["historical_rows"]);print("[COMPARABLE_CASES]",d["comparable_case_count"])
  if d["historical_rows"]<=0:self.fail("NO_CANONICAL_HISTORY_READ")
  print("[PASS] OSI-043B live opportunity -> canonical history bridge")
  print("[TRADER] A real Solana opportunity can now look backward into Oracle's canonical warehouse without future leakage")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-043B LIVE OPPORTUNITY TO CANONICAL HISTORY BRIDGE");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
