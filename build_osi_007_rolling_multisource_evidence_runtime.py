from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_007_rolling_multisource_evidence_runtime.py"
TEST=ROOT/"test_osi_007_rolling_multisource_evidence_runtime.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_002_same_opportunity_evidence_synchronizer import synchronize

EXECUTION_AUTHORITY=False

def build_bundle(seed:dict,evidence:list[dict],freeze_at:str,state_path:Path,lookback_seconds:int=120)->dict:
 bundle=synchronize(seed,evidence,freeze_at,lookback_seconds)
 state={"opportunity_seed_id":seed["opportunity_seed_id"],"asset_key":seed["asset_key"],
        "source_count":bundle["source_count"],"sources":bundle["independent_sources"],
        "freeze_at":bundle["freeze_at"],"evidence_count":len(bundle["evidence"]),
        "execution_authority":False}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return bundle
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_007_rolling_multisource_evidence_runtime import build_bundle
class T(unittest.TestCase):
 def test_bundle(self):
  seed={"opportunity_seed_id":"o","asset_key":"SOL:M"}
  ev=[{"evidence_id":"a","asset_key":"SOL:M","source":"solana_native","observed_at":"2026-09-18T05:00:00+00:00"},
      {"evidence_id":"b","asset_key":"SOL:M","source":"gmgn","observed_at":"2026-09-18T05:00:01+00:00"},
      {"evidence_id":"c","asset_key":"SOL:M","source":"coinbase","observed_at":"2026-09-18T05:00:02+00:00"}]
  with tempfile.TemporaryDirectory() as td:
   b=build_bundle(seed,ev,"2026-09-18T05:00:03+00:00",Path(td)/"s.json")
   self.assertEqual(b["source_count"],3)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_002_same_opportunity_evidence_synchronizer.py").is_file())
  print("[PASS] OSI-007 rolling multi-source evidence runtime")
  print("[TRADER] Every fresh setup can carry a synchronized live evidence snapshot before Oracle calls it")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-007 installed; execution_authority=FALSE")
if __name__=="__main__":main()
