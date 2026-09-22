from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002m_consolidated_physical_history_to_price_paths_closeout.py"
TEST=ROOT/"test_ssi_002m_consolidated_physical_history_to_price_paths_closeout.py"
MODULE=r"""
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import activate_and_verify_temporal_history
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
H=(5,15,30,60,300)
def _rolling_cases(rows):
 out={}; ordered=tuple(rows)
 for n in range(2,len(ordered)):
  frozen=ordered[:n]
  for c in build_outcome_pending_solana_cases(frozen,horizons=H):
   out[(c.experience_id,c.horizon_seconds)]=c
 return tuple(out.values())
def closeout(root=None,cycles=75):
 root=Path(root or Path.cwd()).resolve()
 print("[PHASE-1] activating certified pinned temporal history")
 a=activate_and_verify_temporal_history(root=root,cycles=max(75,int(cycles)),acquisition_seconds=5.0,
  acquisition_timeout_seconds=20.0,persistence_timeout_seconds=45.0,progress=print)
 print("[ACTIVATION]",a)
 if a.successful_cycles < 75: raise AssertionError("certified acquisition did not complete 75 successful cycles")
 token=str(a.token_address);rows=tuple(read_pinned_pool_history(token,root=root,limit=4096))
 print("[PHASE-2]",{"token":token,"history_rows":len(rows),"first":str(rows[0].observed_at) if rows else None,
  "last":str(rows[-1].observed_at) if rows else None})
 if len(rows)<2: raise AssertionError("durable pinned history did not accumulate")
 cases=_rolling_cases(rows)
 print("[PHASE-3]",{"rolling_frozen_cases":len(cases)})
 if not cases: raise AssertionError("rolling pre-outcome prefixes produced no cases")
 paths=materialize_exact_future_price_paths(cases,rows,H,8.0)
 byh={h:sum(1 for p in paths if p.horizon_seconds==h) for h in H}
 print("[PHASE-4]",{"paths":len(paths),"by_horizon":byh})
 if not paths: raise AssertionError("no exact future price paths materialized")
 r={"token":token,"history_rows":len(rows),"cases":len(cases),"paths":len(paths),"by_horizon":byh,
  "pairs":tuple(sorted({p.pair_address for p in paths})),"mfe_min":min(p.mfe for p in paths),
  "mfe_max":max(p.mfe for p in paths),"mae_min":min(p.mae for p in paths),"mae_max":max(p.mae for p in paths),
  "return_min":min(p.return_fraction for p in paths),"return_max":max(p.return_fraction for p in paths),
  "sample_lineage":paths[0].evidence_observation_ids[:12],"read_only":True,"execution_authority":False}
 print("[SSI-002-PHYSICAL-CERTIFIED]",r);return r
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002m_consolidated_physical_history_to_price_paths_closeout import closeout
class T(unittest.TestCase):
 def test_consolidated_physical_closeout(self):
  r=closeout()
  self.assertGreaterEqual(r["history_rows"],2);self.assertGreater(r["cases"],0);self.assertGreater(r["paths"],0)
  self.assertTrue(r["pairs"]);self.assertTrue(r["sample_lineage"]);self.assertTrue(any(r["by_horizon"].values()))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002M CONSOLIDATED PHYSICAL HISTORY -> EXACT FUTURE PRICE-PATH CLOSEOUT INSTALLER");print("="*120)
 deps=[
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] inspected-repo design: OAD-312 pins one token and persists every OAD-275 cycle through OAD-273")
 print("[PASS] rolling frozen prefixes prevent future evidence from entering case formation")
 print("[PASS] full later history is used only for exact future-path outcomes")
 print("[PASS] no direct PostgreSQL, no GMGN, no execution authority")
 print("[DONE] SSI-002M CONSOLIDATED CLOSEOUT INSTALLED")
if __name__=="__main__":main()
