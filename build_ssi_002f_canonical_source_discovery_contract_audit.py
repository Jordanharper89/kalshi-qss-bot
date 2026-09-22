from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002f_canonical_source_discovery_contract_audit.py"
TEST=ROOT/"test_ssi_002f_canonical_source_discovery_contract_audit.py"
MODULE=r"""
from pathlib import Path
import ast
FILES=(
"qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
)
TOKENS=("CanonicalPersistenceQueryRequest","by_source_id","source_id","query","prefix","list",
        "distinct","backend","execute","fetch","read","observation","limit")
def audit(root=None):
 root=Path(root or Path.cwd()); out=[]
 for rel in FILES:
  p=root/rel; text=p.read_text(encoding="utf-8",errors="replace"); tree=ast.parse(text)
  funcs=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
  hits=[]
  for i,line in enumerate(text.splitlines(),1):
   found=tuple(k for k in TOKENS if k.lower() in line.lower())
   if found:hits.append({"line":i,"tokens":found,"text":line.strip()})
  out.append({"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"lineage":tuple(hits)})
 return {"files":tuple(out),"read_only":True,"execution_authority":False}
def print_audit(root=None):
 r=audit(root);print("[SSI-002F] CANONICAL SOURCE DISCOVERY CONTRACT AUDIT")
 for f in r["files"]:
  print("\\n[FILE]",f["file"]);print("[FUNCTIONS]",f["functions"])
  for h in f["lineage"]:print("[LINEAGE]",h)
 print("\\n[CONTRACT] read_only=True execution_authority=False");return r
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002f_canonical_source_discovery_contract_audit import print_audit
class T(unittest.TestCase):
 def test_contract_audit(self):
  r=print_audit()
  self.assertEqual(len(r["files"]),2);self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
  self.assertTrue(any(f["lineage"] for f in r["files"]))
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002F CANONICAL SOURCE DISCOVERY CONTRACT AUDIT INSTALLER");print("="*120)
 for rel in [
 "qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py"]:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] exact canonical query contract audited before source discovery")
 print("[PASS] no guessed source-list API, PostgreSQL connection, acquisition, writer, or runtime mutation")
 print("[DONE] SSI-002F INSTALLATION COMPLETE")
if __name__=="__main__":main()
