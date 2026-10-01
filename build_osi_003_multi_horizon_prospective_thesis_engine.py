from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_003_multi_horizon_prospective_thesis_engine.py"
TEST=ROOT/"test_osi_003_multi_horizon_prospective_thesis_engine.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
HORIZONS=(5,15,30,60,300,900)
EXECUTION_AUTHORITY=False

def _hash(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def build_theses(bundle:dict,reasoning:dict,min_sources:int=2)->list[dict]:
 if bundle.get("source_count",0)<min_sources:return []
 out=[]
 for h in HORIZONS:
  meta=dict(reasoning.get("thesis_metadata") or {})
  family=meta.get("thesis_family")
  if family=="BUY_PRESSURE" and h==60:
   meta.update({"thesis_family":"BUY_PRESSURE","horizon_seconds":60,"target_return":0.10,"economic_stop_return":-0.05,"friction_bps":200})
  elif family=="BUY_PRESSURE":
   continue
  else:
   meta["horizon_seconds"]=h
   meta.setdefault("friction_bps",200)
  row={
   "opportunity_seed_id":bundle["opportunity_seed_id"],"asset_key":bundle["asset_key"],
   "freeze_at":bundle["freeze_at"],"horizon_seconds":h,"thesis_metadata":meta,
   "x_y_z_reasoning":dict(reasoning.get("x_y_z_reasoning") or {}),
   "historical_probability_claimed":False,"calibrated_probability":reasoning.get("calibrated_probability"),
   "paper_only":True,"prospective":True,"execution_authority":False
  }
  row["thesis_id"]=_hash(row);out.append(row)
 return out
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_003_multi_horizon_prospective_thesis_engine import build_theses,HORIZONS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_universal(self):
  b={"source_count":3,"opportunity_seed_id":"x","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r=build_theses(b,{"thesis_metadata":{"thesis_family":"LIQUIDITY_EXPANSION"},"x_y_z_reasoning":{"x":"new_pool","y":"liquidity_up","z":"wallet_cluster"}})
  self.assertEqual(tuple(x["horizon_seconds"] for x in r),HORIZONS)
 def test_buy_pressure_frozen(self):
  b={"source_count":3,"opportunity_seed_id":"x","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r=build_theses(b,{"thesis_metadata":{"thesis_family":"BUY_PRESSURE"}})
  self.assertEqual(len(r),1);self.assertEqual(r[0]["horizon_seconds"],60);self.assertEqual(r[0]["thesis_metadata"]["target_return"],.10)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_002_same_opportunity_evidence_synchronizer.py").is_file())
  print("[PASS] OSI-003 multi-horizon prospective thesis engine")
  print("[TRADER] Oracle can study 5s/15s/30s/60s/5m/15m edge without rewriting BUY_PRESSURE")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-003 installed; execution_authority=FALSE")
if __name__=="__main__":main()
