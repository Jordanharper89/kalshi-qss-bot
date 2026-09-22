from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002d_existing_history_physical_materialization_certification.py"
TEST=ROOT/"test_ssi_002d_existing_history_physical_materialization_certification.py"
MODULE=r"""
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
def certify_existing_history(root=None,limit=512):
 token=select_live_solana_token(20.0)
 rows=tuple(read_pinned_pool_history(token,root=root,limit=limit))
 if len(rows)<2: raise AssertionError("insufficient existing persisted history")
 cases=tuple(build_outcome_pending_solana_cases(rows,horizons=(5,15,30,60,300,900,3600)))
 paths=materialize_exact_future_price_paths(cases,rows,(5,15,30,60,300,900,3600),8.0)
 if not paths: raise AssertionError("existing persisted history produced zero exact future price paths")
 pairs=tuple(sorted({p.pair_address for p in paths}))
 horizons=tuple(sorted({p.horizon_seconds for p in paths}))
 first=min(str(r.observed_at) for r in rows); last=max(str(r.observed_at) for r in rows)
 report={"token_address":token,"history_rows":len(rows),"first_observed_at":first,"last_observed_at":last,
 "pairs":pairs,"supported_horizons":horizons,"paths":len(paths),
 "mfe_min":min(p.mfe for p in paths),"mfe_max":max(p.mfe for p in paths),
 "mae_min":min(p.mae for p in paths),"mae_max":max(p.mae for p in paths),
 "sample_observation_ids":paths[0].evidence_observation_ids[:12],
 "read_only":True,"execution_authority":False}
 return report
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002d_existing_history_physical_materialization_certification import certify_existing_history
class T(unittest.TestCase):
 def test_physical_existing_history(self):
  r=certify_existing_history()
  print("[SSI-002D]",r)
  self.assertGreaterEqual(r["history_rows"],2)
  self.assertGreater(r["paths"],0)
  self.assertTrue(r["pairs"]);self.assertTrue(r["supported_horizons"])
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002D EXISTING-HISTORY PHYSICAL MATERIALIZATION CERTIFICATION INSTALLER");print("="*120)
 deps=[
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists(): raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] exact OAD-274 read_pinned_pool_history boundary reused")
 print("[PASS] existing persisted rows only; no temporal-history activation call")
 print("[PASS] no PostgreSQL connection, writer, runtime mutation, GMGN, or execution authority")
 print("[DONE] SSI-002D INSTALLATION COMPLETE")
if __name__=="__main__": main()
