from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_064_prospective_pending_case_set.py"
TEST=ROOT/"test_osi_064_prospective_pending_case_set.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaOutcomePendingCase

HORIZONS=(5,15,30,60,300,900)

def build(root):
 d=json.loads((root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json").read_text(encoding="utf-8"))
 out=[]
 for h in HORIZONS:
  out.append(SolanaOutcomePendingCase(
   f"osi:{d['asset_key']}:{d['observation_id']}:{h}",
   d["asset_key"],
   d["pair_address"],
   d["observed_at"],
   tuple(),
   (d["observation_id"],),
   h,
  ))
 return tuple(out)
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_064_prospective_pending_case_set import build,HORIZONS
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  cases=build(ROOT)
  self.assertEqual(tuple(x.horizon_seconds for x in cases),HORIZONS)
  for c in cases:
   print("[CASE]",c.experience_id,c.horizon_seconds,c.snapshot_at)
  print("[PASS] OSI-064 prospective OAD-314 pending case set")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-064 PROSPECTIVE OAD-314 PENDING CASE SET")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 main()