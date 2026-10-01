from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_055_oad314_case_record_contract_audit.py"
TEST=ROOT/"test_osi_055b_oad314_case_record_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import ast,json
from pathlib import Path

TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
FUNC="attribute_forward_outcomes"

def _const_str(node):
 if isinstance(node,ast.Constant) and isinstance(node.value,str):
  return node.value
 return None

def audit(root:Path)->dict:
 p=root/TARGET
 if not p.is_file():
  raise RuntimeError("Missing OAD-314 module")
 text=p.read_text(encoding="utf-8",errors="replace")
 tree=ast.parse(text)
 fn=None
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==FUNC:
   fn=n;break
 if fn is None:
  raise RuntimeError("Missing attribute_forward_outcomes")

 gets=[]
 subscripts=[]
 loops=[]
 calls=[]
 for n in ast.walk(fn):
  if isinstance(n,ast.For):
   loops.append(ast.get_source_segment(text,n)[:1200])
  elif isinstance(n,ast.Call):
   calls.append(ast.get_source_segment(text,n)[:900])
   if isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args:
    k=_const_str(n.args[0])
    if k:
     owner=ast.get_source_segment(text,n.func.value) or "?"
     gets.append({"owner":owner,"key":k,"line":n.lineno})
  elif isinstance(n,ast.Subscript):
   k=_const_str(n.slice)
   if k:
    owner=ast.get_source_segment(text,n.value) or "?"
    subscripts.append({"owner":owner,"key":k,"line":n.lineno})

 return {
  "revision":"OSI_055B",
  "module":TARGET,
  "function":FUNC,
  "signature_args":[a.arg for a in fn.args.args],
  "dict_gets":gets,
  "subscripts":subscripts,
  "loops":loops[:50],
  "calls":calls[:100],
  "execution_authority":False,
  "read_only":True,
 }

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/oad314_case_record_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad314_case_record_contract_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  self.assertEqual(d["function"],"attribute_forward_outcomes")
  print("[SIGNATURE_ARGS]",d["signature_args"])
  print("[DICT_GETS]",json.dumps(d["dict_gets"],sort_keys=True))
  print("[SUBSCRIPTS]",json.dumps(d["subscripts"],sort_keys=True))
  print("[LOOPS]",json.dumps(d["loops"][:12],sort_keys=True))
  print("[CALLS]",json.dumps(d["calls"][:20],sort_keys=True))
  if not d["dict_gets"] and not d["subscripts"]:
   self.fail("NO_OAD314_CASE_RECORD_FIELD_CONTRACT_FOUND")
  print("[PASS] OSI-055B OAD-314 exact case/record contract audit")
  print("[TRADER] Extracts the exact fields OAD-314 expects from candidate cases and temporal records")
  print("[SCOPE] Read-only source audit; no guessed shared-key contract")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-055B OAD-314 EXACT CASE / RECORD CONTRACT AUDIT")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement for failed OSI-055 flat-key intersection audit")

if __name__=="__main__":
 main()
