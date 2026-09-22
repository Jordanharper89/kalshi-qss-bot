from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002e_persisted_solana_history_identity_reader_diagnostic.py"
TEST=ROOT/"test_ssi_002e_persisted_solana_history_identity_reader_diagnostic.py"
MODULE=r"""
from pathlib import Path
import ast
FILES=(
"qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
)
TOKENS=("token_address","pair_address","observation_id","read_pinned_pool_history","persist",
        "postgres","sql","where","payload","pools","source_id","observation_type","limit")
def diagnose(root=None):
 root=Path(root or Path.cwd()); report=[]
 for rel in FILES:
  p=root/rel
  text=p.read_text(encoding="utf-8",errors="replace")
  tree=ast.parse(text); funcs=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
  hits=[]
  for i,line in enumerate(text.splitlines(),1):
   low=line.lower()
   found=tuple(k for k in TOKENS if k in low)
   if found: hits.append({"line":i,"tokens":found,"text":line.strip()})
  report.append({"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"lineage":tuple(hits)})
 return {"files":tuple(report),"read_only":True,"execution_authority":False}
def print_diagnostic(root=None):
 r=diagnose(root)
 print("[SSI-002E] PERSISTED SOLANA HISTORY IDENTITY / READER DIAGNOSTIC")
 for f in r["files"]:
  print("\\n[FILE]",f["file"]);print("[FUNCTIONS]",f["functions"])
  for h in f["lineage"]: print("[LINEAGE]",h)
 print("\\n[CONTRACT] read_only=True execution_authority=False")
 return r
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002e_persisted_solana_history_identity_reader_diagnostic import print_diagnostic
class T(unittest.TestCase):
 def test_repository_diagnostic(self):
  r=print_diagnostic()
  self.assertEqual(len(r["files"]),2)
  self.assertTrue(any(any(x["tokens"] for x in f["lineage"]) for f in r["files"]))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002E PERSISTED SOLANA HISTORY IDENTITY / READER DIAGNOSTIC INSTALLER");print("="*120)
 for rel in [
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py"]:
  q=ROOT/rel
  if not q.exists(): raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] repository/source diagnostic only -- no live token selection")
 print("[PASS] no PostgreSQL connection, acquisition, writer, runtime mutation, GMGN, or execution authority")
 print("[DONE] SSI-002E INSTALLATION COMPLETE")
if __name__=="__main__": main()
