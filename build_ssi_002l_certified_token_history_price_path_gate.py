from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002l_certified_token_history_price_path_gate.py"
TEST=ROOT/"test_ssi_002l_certified_token_history_price_path_gate.py"
MODULE=r"""
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
TOKENS=("2R3MTHtRM3BDvMyfktavqwHpsiCBRnMugvDj4ZiKpump","7eGWP35VMUqKTHbyTwZhv8aVcCK2iePaz1ju3nZrpump")
H=(5,15,30,60,300,900,3600)
def certify(root=None,limit=10000):
 attempts=[]
 for token in TOKENS:
  rows=tuple(read_pinned_pool_history(token,root=root,limit=limit))
  cases=tuple(build_outcome_pending_solana_cases(rows,horizons=H))
  paths=materialize_exact_future_price_paths(cases,rows,H,8.0)
  attempts.append({"token":token,"rows":len(rows),"cases":len(cases),"paths":len(paths)})
  print("[TOKEN]",attempts[-1])
  if paths:
   p=paths[0];r={"token":token,"history_rows":len(rows),"cases":len(cases),"paths":len(paths),
    "pairs":tuple(sorted({x.pair_address for x in paths})),"horizons":tuple(sorted({x.horizon_seconds for x in paths})),
    "first_observed_at":str(rows[0].observed_at),"last_observed_at":str(rows[-1].observed_at),
    "mfe_min":min(x.mfe for x in paths),"mfe_max":max(x.mfe for x in paths),
    "mae_min":min(x.mae for x in paths),"mae_max":max(x.mae for x in paths),
    "sample_lineage":p.evidence_observation_ids[:12],"attempts":tuple(attempts),"read_only":True,"execution_authority":False}
   print("[SSI-002-PHYSICAL-CERTIFIED]",r);return r
 print("[ATTEMPTS]",tuple(attempts))
 raise AssertionError("SSI-002K-certified token sources contain no exact future price path")
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002l_certified_token_history_price_path_gate import certify
class T(unittest.TestCase):
 def test_physical_price_path(self):
  r=certify();self.assertGreater(r["history_rows"],1);self.assertGreater(r["paths"],0)
  self.assertTrue(r["pairs"]);self.assertTrue(r["horizons"]);self.assertTrue(r["sample_lineage"])
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002L CERTIFIED TOKEN HISTORY -> PHYSICAL PRICE-PATH GATE INSTALLER");print("="*120)
 deps=["qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py","qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py","qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] consumes exact SSI-002K-certified persisted token identities through OAD-274")
 print("[PASS] existing history only; no acquisition, writer, GMGN, direct PostgreSQL, or execution authority")
 print("[DONE] SSI-002L INSTALLATION COMPLETE")
if __name__=="__main__":main()
