from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_066_physical_oad314_forward_outcome_attribution.py"
TEST=ROOT/"test_osi_066b_nonblocking_physical_oad314_attribution.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import attribute_forward_outcomes
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_064_prospective_pending_case_set import build

def _obj(d):
 return SolanaHistoricalObservation(
  d["observation_id"],d["source_id"],d["observation_type"],d["observed_at"],
  d.get("sequence_number"),d.get("provider"),d.get("subject"),d["payload"]
 )

def run(root,tolerance_seconds=8.0):
 cases=build(root)
 data=json.loads((root/"runtime_state/solana_opportunities/outcomes/nonblocking_native_temporal_records.json").read_text(encoding="utf-8"))
 records=tuple(_obj(x) for x in data["records"])
 outcomes=tuple(attribute_forward_outcomes(cases,records,tolerance_seconds=tolerance_seconds))
 rows=[asdict(x) for x in outcomes];resolved=sorted({int(x["horizon_seconds"]) for x in rows})
 return {"revision":"OSI_066B","asset_key":cases[0].token_address,"record_count":len(records),
  "verified_outcomes":len(rows),"resolved_horizons":resolved,"outcomes":rows,"execution_authority":False}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/outcomes/verified_forward_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_066_physical_oad314_forward_outcome_attribution import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[RECORD_COUNT]",d["record_count"]);print("[VERIFIED_OUTCOMES]",d["verified_outcomes"]);print("[RESOLVED_HORIZONS]",d["resolved_horizons"])
  for x in d["outcomes"]:print("[OUTCOME]",json.dumps(x,sort_keys=True))
  if d["verified_outcomes"]==0:self.fail("OAD314_PRODUCED_NO_REAL_NONBLOCKING_OUTCOMES")
  print("[PASS] OSI-066B physical OAD-314 attribution from nonblocking native records")
  print("[TRADER] OAD-314 graded real future prices against the exact prospective anchor")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" OSI-066B NONBLOCKING PHYSICAL OAD-314 ATTRIBUTION");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
