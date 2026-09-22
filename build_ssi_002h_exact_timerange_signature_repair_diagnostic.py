from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002h_exact_timerange_signature_repair_diagnostic.py"
TEST=ROOT/"test_ssi_002h_exact_timerange_signature_repair_diagnostic.py"
MODULE=r"""
import inspect
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
def diagnose():
 fn=CanonicalPersistenceQueryRequest.by_observed_time_range
 sig=str(inspect.signature(fn))
 print("[SSI-002H] by_observed_time_range signature =",sig)
 return {"signature":sig,"read_only":True,"execution_authority":False}
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002h_exact_timerange_signature_repair_diagnostic import diagnose
class T(unittest.TestCase):
 def test_signature(self):
  r=diagnose()
  self.assertIn("by_observed_time_range",str(__import__("qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract",fromlist=["CanonicalPersistenceQueryRequest"]).CanonicalPersistenceQueryRequest.by_observed_time_range))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002H EXACT TIME-RANGE SIGNATURE REPAIR DIAGNOSTIC INSTALLER");print("="*120)
 rel="qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py"
 q=ROOT/rel
 if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
 ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] runtime signature introspection only; SSI-002G remains uncertified")
 print("[DONE] SSI-002H INSTALLATION COMPLETE")
if __name__=="__main__":main()
