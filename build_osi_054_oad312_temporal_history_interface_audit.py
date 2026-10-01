from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_054_oad312_temporal_history_interface_audit.py"
TEST=ROOT/"test_osi_054_oad312_temporal_history_interface_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json
from pathlib import Path
TARGET="qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py"
def audit(root):
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing OAD-312")
 text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
 funcs=[];constants=[];strings=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   funcs.append({"name":n.name,"line":n.lineno,"args":[a.arg for a in n.args.args]})
  elif isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name):constants.append({"name":t.id,"value":ast.get_source_segment(text,n.value)[:700]})
  elif isinstance(n,ast.Constant) and isinstance(n.value,str):
   s=n.value.strip()
   if any(k in s.lower() for k in ("history","temporal","runtime","json","jsonl","slot","price","pool","mint")):strings.append(s)
 return {"revision":"OSI_054","module":TARGET,"functions":funcs,"constants":constants[:200],"strings":strings[:300],"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/oad312_temporal_history_interface.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_054_oad312_temporal_history_interface_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertGreater(len(d["functions"]),0)
  print("[FUNCTIONS]",json.dumps(d["functions"],sort_keys=True))
  print("[STRINGS]",json.dumps(d["strings"][:30],sort_keys=True))
  print("[PASS] OSI-054 OAD-312 temporal-history interface audit")
  print("[TRADER] Finds the exact historical price/path input OAD-314 can grade")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-054 OAD-312 TEMPORAL-HISTORY INTERFACE AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
