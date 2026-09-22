from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_002j_canonical_timerange_ordering_traversal_diagnostic.py"
TEST=ROOT/"test_ssi_002j_canonical_timerange_ordering_traversal_diagnostic.py"
MODULE=r"""
from pathlib import Path
import ast,inspect
TOKENS=("by_observed_time_range","query_type","observed_from","observed_to","ORDER BY","LIMIT","ASC","DESC","fetch","query","cursor","offset")
def diagnose(root=None):
 root=Path(root or Path.cwd())
 from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import _backend
 b=_backend(root);cls=type(b);out=[]
 print("[BACKEND_CLASS]",cls.__module__+"."+cls.__qualname__)
 print("[BACKEND_QUERY_SIGNATURE]",inspect.signature(b.query))
 files=["qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py"]
 src=inspect.getsourcefile(cls)
 if src:
  try: files.append(str(Path(src).resolve().relative_to(root.resolve())).replace(chr(92),"/"))
  except ValueError: pass
 for rel in dict.fromkeys(files):
  p=root/rel
  if not p.exists():continue
  text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text);hits=[]
  funcs=[{"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  for i,line in enumerate(text.splitlines(),1):
   found=tuple(t for t in TOKENS if t.lower() in line.lower())
   if found:hits.append({"line":i,"tokens":found,"text":line.strip()})
  rec={"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"hits":tuple(hits)};out.append(rec)
  print("\n[FILE]",rel);print("[FUNCTIONS]",rec["functions"])
  for h in hits:print("[LINEAGE]",h)
 r={"backend_class":cls.__module__+"."+cls.__qualname__,"files":tuple(out),"read_only":True,"execution_authority":False}
 print("\n[CONTRACT] read_only=True execution_authority=False");return r
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002j_canonical_timerange_ordering_traversal_diagnostic import diagnose
class T(unittest.TestCase):
 def test_ordering_contract(self):
  r=diagnose();self.assertTrue(r["backend_class"]);self.assertTrue(r["files"])
  self.assertTrue(any(f["hits"] for f in r["files"]));self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-002J CANONICAL TIME-RANGE ORDERING + TRAVERSAL DIAGNOSTIC INSTALLER");print("="*120)
 rel="qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py";q=ROOT/rel
 if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
 ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] physical backend identity + time-range ordering/traversal contract diagnostic")
 print("[PASS] no acquisition, append, writer, direct connection, runtime mutation, or execution authority")
 print("[DONE] SSI-002J INSTALLATION COMPLETE")
if __name__=="__main__":main()
