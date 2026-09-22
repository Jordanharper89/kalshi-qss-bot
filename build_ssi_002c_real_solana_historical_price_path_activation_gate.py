from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002c_real_solana_historical_price_path_activation_gate.py"
TEST=ROOT/"test_ssi_002c_real_solana_historical_price_path_activation_gate.py"
MODULE=r"""
from pathlib import Path
import importlib,inspect
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
CANDIDATES=(
"qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence",
"qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows",
"qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate",
)
KEYS=("read","history","record","snapshot","window","persist","observation")
def audit_interfaces():
 out=[]
 for modname in CANDIDATES:
  m=importlib.import_module(modname)
  funcs=[]
  for name,obj in inspect.getmembers(m,inspect.isfunction):
   if obj.__module__==modname and any(k in name.lower() for k in KEYS):
    try:sig=str(inspect.signature(obj))
    except Exception:sig="?"
    funcs.append((name,sig))
  out.append((modname,tuple(funcs)))
 return tuple(out)
def run_gate():
 interfaces=audit_interfaces()
 print("[REAL_HISTORY_INTERFACES]")
 for mod,funcs in interfaces:
  print("[MODULE]",mod)
  for f in funcs: print("[FUNCTION]",f)
 readers=[]
 for mod,funcs in interfaces:
  for name,sig in funcs:
   if any(k in name.lower() for k in ("read","history","record","window")):
    readers.append((mod,name,sig))
 return {"interfaces":interfaces,"candidate_readers":tuple(readers),
         "exact_materializer":materialize_exact_future_price_paths.__name__,
         "production_history_reader_found":bool(readers),
         "read_only":True,"execution_authority":False}
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002c_real_solana_historical_price_path_activation_gate import run_gate
class T(unittest.TestCase):
 def test_real_history_boundary(self):
  r=run_gate()
  print("[CANDIDATE_READERS]",r["candidate_readers"])
  print("[GATE] production_history_reader_found=",r["production_history_reader_found"])
  self.assertTrue(r["interfaces"])
  self.assertFalse(r["execution_authority"])
  self.assertTrue(r["read_only"])
  self.assertTrue(r["production_history_reader_found"],
   "No certified existing Solana temporal-history reader was discoverable; wire exact discovered interface before physical path activation.")
if __name__=="__main__": unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002C REAL SOLANA HISTORICAL PRICE-PATH ACTIVATION GATE INSTALLER");print("="*120)
 deps=[
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py",
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists(): raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] exact existing Solana history interfaces will be introspected before invocation")
 print("[PASS] no guessed PostgreSQL/reader signature")
 print("[PASS] no acquisition, writer, runtime mutation, GMGN, or execution authority")
 print("[DONE] SSI-002C INSTALLATION COMPLETE")
if __name__=="__main__": main()
