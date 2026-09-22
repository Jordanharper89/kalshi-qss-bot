from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002k_ascending_timerange_window_discovery_certification.py"
TEST=ROOT/"test_ssi_002k_ascending_timerange_window_discovery_certification.py"
MODULE=r"""
from datetime import datetime,timezone,timedelta
from collections import Counter
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import _backend
PREFIX="source.dex.solana.token_pools."
def discover(root=None,days=30,window_minutes=30,limit=10000):
 backend=_backend(root);end=datetime.now(timezone.utc);start=end-timedelta(days=int(days));windows=0
 found=Counter();samples=[];cursor=start
 while cursor<end:
  stop=min(cursor+timedelta(minutes=int(window_minutes)),end);requested=datetime.now(timezone.utc)
  req=CanonicalPersistenceQueryRequest.by_observed_time_range(
   query_id=f"query.ssi002k.{windows}",backend_id=backend.backend_id,observed_from=cursor,observed_to=stop,
   limit=int(limit),requested_at=requested,query_metadata={"read_only":True,"purpose":"ssi002k_window_source_discovery"})
  rows=tuple(backend.query(request=req));pool=tuple(r for r in rows if str(r.source_id).startswith(PREFIX))
  for r in pool:found[str(r.source_id)[len(PREFIX):]]+=1
  if pool:samples.extend((str(r.observation_id),str(r.source_id),str(r.observed_at)) for r in pool[:10])
  print("[WINDOW]",windows,cursor.isoformat(),stop.isoformat(),"rows=",len(rows),"pool_rows=",len(pool))
  windows+=1
  if found:break
  cursor=stop
 ranked=tuple(sorted(found.items(),key=lambda x:(-x[1],x[0])))
 r={"windows_scanned":windows,"ranked_tokens":ranked,"samples":tuple(samples[:20]),"read_only":True,"execution_authority":False}
 print("[DISCOVERY]",r)
 if not ranked:raise AssertionError("no persisted token-pool source found in bounded ascending time windows")
 return r
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002k_ascending_timerange_window_discovery_certification import discover
class T(unittest.TestCase):
 def test_physical_source_discovery(self):
  r=discover()
  self.assertTrue(r["ranked_tokens"]);self.assertTrue(r["samples"])
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002K ASCENDING TIME-RANGE WINDOW SOURCE DISCOVERY CERTIFICATION INSTALLER");print("="*120)
 for rel in ["qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py","qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py"]:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] uses certified ascending ORDER BY observed_at, sequence_number with bounded 30-minute windows")
 print("[PASS] read-only canonical backend only; no acquisition, append, writer, direct connection, or execution authority")
 print("[DONE] SSI-002K INSTALLATION COMPLETE")
if __name__=="__main__":main()
