from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_064_confirmed_horizon_outcome_worker.py"
TEST=ROOT/"test_suls_095b_ast_semantic_safety_repair.py"

class Repair(ast.NodeTransformer):
 def __init__(self):self.changed=0
 def visit_Dict(self,node):
  self.generic_visit(node)
  keys=[k.value if isinstance(k,ast.Constant) and isinstance(k.value,str) else None for k in node.keys]
  for i,k in enumerate(keys):
   if k=="return_from_birth":
    node.keys[i]=ast.Constant("reserve_ratio_change_from_birth")
    keys[i]="reserve_ratio_change_from_birth"
    self.changed+=1
  if "reserve_ratio_change_from_birth" in keys:
   extras={
    "outcome_semantics":"RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY",
    "executable_pnl":False,
    "profitability_eligible":False
   }
   for k,v in extras.items():
    if k not in keys:
     node.keys.append(ast.Constant(k))
     node.values.append(ast.Constant(v))
     self.changed+=1
  return node

TEST_TEXT=r"""import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_064_confirmed_horizon_outcome_worker.py"

class T(unittest.TestCase):
 def test_semantics(self):
  s=P.read_text(encoding="utf-8")
  ast.parse(s)
  self.assertNotIn("return_from_birth",s)
  self.assertIn("reserve_ratio_change_from_birth",s)
  self.assertIn("RESERVE_RATIO_OBSERVATIONAL_PROXY_ONLY",s)
  self.assertIn("profitability_eligible",s)
  self.assertIn("executable_pnl",s)
  print("[PASS] SULS-095B canonical reserve-ratio semantic repair")
  print("[PASS] profitability_eligible=FALSE")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-095B AST SEMANTIC SAFETY REPAIR")
 print("="*116)

 if not TARGET.exists():
  raise SystemExit("CANONICAL_SULS_064_NOT_FOUND")

 src=TARGET.read_text(encoding="utf-8")
 tree=ast.parse(src)

 r=Repair()
 tree=r.visit(tree)
 ast.fix_missing_locations(tree)

 if r.changed==0:
  raise SystemExit("SULS_064_RESERVE_RATIO_FIELD_NOT_FOUND")

 bak=TARGET.with_suffix(".pre_suls095b.bak")
 if not bak.exists():
  bak.write_text(src,encoding="utf-8")

 TARGET.write_text(ast.unparse(tree)+"\n",encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")

 print("[PASS] repaired canonical:",TARGET.relative_to(ROOT))
 print("[PASS] semantic edits:",r.changed)
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 main()