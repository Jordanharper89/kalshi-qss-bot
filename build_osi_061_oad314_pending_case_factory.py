from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_061_oad314_pending_case_factory.py"
TEST=ROOT/"test_osi_061_oad314_pending_case_factory.py"
MOD_TEXT=r"""from __future__ import annotations
import json,uuid
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaOutcomePendingCase
HORIZONS=(5,15,30,60,300,900)
def build(root):
 p=root/"runtime_state/solana_opportunities/live_token_pair_resolution.json";d=json.loads(p.read_text(encoding="utf-8"))
 if not d.get("matches"):raise RuntimeError("NO_RESOLVED_PAIR_MATCH")
 m=next((x for x in d["matches"] if x.get("pair_address")),None)
 if m is None:raise RuntimeError("NO_PAIR_ADDRESS_IN_RESOLVED_HISTORY")
 asset=d["asset_key"];cases=[]
 for h in HORIZONS:
  eid=f"osi:{asset}:{m['observation_id']}:{h}"
  cases.append(SolanaOutcomePendingCase(eid,asset,str(m["pair_address"]),m["observed_at"],tuple(),(m["observation_id"],),h))
 return {"revision":"OSI_061","asset_key":asset,"pair_address":str(m["pair_address"]),"anchor_observation_id":m["observation_id"],"cases":cases,"case_count":len(cases),"execution_authority":False}
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_061_oad314_pending_case_factory import build,HORIZONS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=build(ROOT);self.assertEqual(d["case_count"],len(HORIZONS));self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"]);print("[PAIR]",d["pair_address"]);print("[ANCHOR_OBSERVATION]",d["anchor_observation_id"])
  for c in d["cases"]:print("[CASE]",c.experience_id,c.horizon_seconds,c.snapshot_at)
  print("[PASS] OSI-061 OAD-314 pending-case factory")
  print("[TRADER] Builds real 5s/15s/30s/60s/5m/15m outcome-pending cases from the resolved live token")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" OSI-061 OAD-314 PENDING CASE FACTORY");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()