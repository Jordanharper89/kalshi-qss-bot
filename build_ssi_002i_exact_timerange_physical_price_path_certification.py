from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002i_exact_timerange_physical_price_path_certification.py"
TEST=ROOT/"test_ssi_002i_exact_timerange_physical_price_path_certification.py"
MODULE=r"""
from datetime import datetime,timezone,timedelta
from collections import Counter
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import _backend
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
PREFIX="source.dex.solana.token_pools."
def certify(root=None,lookback_hours=336,scan_limit=10000,history_limit=4096):
 backend=_backend(root); requested=datetime.now(timezone.utc)
 start=requested-timedelta(hours=float(lookback_hours))
 req=CanonicalPersistenceQueryRequest.by_observed_time_range(
  query_id="query.ssi002i.solana.token_pool.discovery",backend_id=backend.backend_id,
  observed_from=start,observed_to=requested,limit=int(scan_limit),requested_at=requested,
  query_metadata={"read_only":True,"purpose":"ssi002i_existing_history_discovery"})
 scanned=tuple(backend.query(request=req))
 pool_rows=tuple(r for r in scanned if str(r.source_id).startswith(PREFIX))
 ranked=tuple(sorted(Counter(str(r.source_id)[len(PREFIX):] for r in pool_rows).items(),key=lambda x:(-x[1],x[0])))
 print("[SCAN]",{"all_rows":len(scanned),"token_pool_rows":len(pool_rows),"tokens":len(ranked),
                 "observed_from":start.isoformat(),"observed_to":requested.isoformat()})
 print("[RANKED_TOKENS]",ranked[:20]); attempts=[]
 for token,n in ranked:
  rows=tuple(read_pinned_pool_history(token,root=root,limit=history_limit))
  cases=tuple(build_outcome_pending_solana_cases(rows,horizons=(5,15,30,60,300,900,3600)))
  paths=materialize_exact_future_price_paths(cases,rows,(5,15,30,60,300,900,3600),8.0)
  attempts.append((token,n,len(rows),len(cases),len(paths)))
  if paths:
   r={"token_address":token,"discovery_rows":n,"history_rows":len(rows),"cases":len(cases),"paths":len(paths),
      "pairs":tuple(sorted({p.pair_address for p in paths})),"supported_horizons":tuple(sorted({p.horizon_seconds for p in paths})),
      "first_observed_at":str(rows[0].observed_at),"last_observed_at":str(rows[-1].observed_at),
      "mfe_min":min(p.mfe for p in paths),"mfe_max":max(p.mfe for p in paths),
      "mae_min":min(p.mae for p in paths),"mae_max":max(p.mae for p in paths),
      "sample_observation_ids":paths[0].evidence_observation_ids[:12],"attempts":tuple(attempts),
      "read_only":True,"execution_authority":False}
   print("[CERTIFIED]",r);return r
 print("[ATTEMPTS]",tuple(attempts))
 raise AssertionError("bounded persisted Solana token-pool history produced zero exact future price paths")
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002i_exact_timerange_physical_price_path_certification import certify
class T(unittest.TestCase):
 def test_real_persisted_price_paths(self):
  r=certify()
  self.assertGreater(r["history_rows"],1);self.assertGreater(r["paths"],0)
  self.assertTrue(r["pairs"]);self.assertTrue(r["supported_horizons"])
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002I EXACT TIME-RANGE PHYSICAL PRICE-PATH CERTIFICATION INSTALLER");print("="*120)
 deps=["qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py",
 "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
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
 print("[PASS] exact SSI-002H signature: observed_from / observed_to / requested_at")
 print("[PASS] existing persisted data only; no acquisition, writer, direct PostgreSQL connection, GMGN, or execution authority")
 print("[DONE] SSI-002I INSTALLATION COMPLETE")
if __name__=="__main__":main()
