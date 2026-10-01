from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_053_oad314_callable_interface_audit.py"
TEST=ROOT/"test_osi_053_oad314_callable_interface_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,inspect,json
from pathlib import Path
TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
def audit(root):
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing OAD-314")
 text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
 funcs=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   args=[a.arg for a in n.args.args]
   funcs.append({"name":n.name,"line":n.lineno,"args":args})
 imports=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):imports.append({"module":n.module,"names":[x.name for x in n.names]})
  elif isinstance(n,ast.Import):imports.extend({"module":x.name,"names":[]} for x in n.names)
 returns=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Return):returns.append({"line":n.lineno,"text":ast.get_source_segment(text,n.value)[:1000] if n.value else None})
 return {"revision":"OSI_053","module":TARGET,"functions":funcs,"imports":imports[:200],"returns":returns[:200],"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/oad314_callable_interface.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_053_oad314_callable_interface_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertGreater(len(d["functions"]),0)
  print("[FUNCTIONS]",json.dumps(d["functions"],sort_keys=True))
  print("[RETURNS]",json.dumps(d["returns"][:20],sort_keys=True))
  print("[PASS] OSI-053 OAD-314 callable interface audit")
  print("[TRADER] Finds the exact in-memory function that computes verified future outcomes")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-053 OAD-314 CALLABLE INTERFACE AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
