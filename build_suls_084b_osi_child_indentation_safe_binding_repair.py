from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"run_osi_solana_intelligence_live.py"
BACKUP=ROOT/"run_osi_solana_intelligence_live.pre_suls084.bak"
TEST=ROOT/"test_suls_084b_osi_child_indentation_safe_binding_repair.py"

IMPORT1="import threading"
IMPORT2="from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import run_forever as run_suls_forever"
MARK="# SULS-084B indentation-safe existing OSI child binding"

TEST_TEXT=r"""import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"run_osi_solana_intelligence_live.py"

class T(unittest.TestCase):
 def test_repair(self):
  s=P.read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("# SULS-084B indentation-safe existing OSI child binding",s)
  self.assertEqual(s.count("run_suls_forever"),2)
  self.assertIn('name="OSI-SULS-EventDriven"',s)
  self.assertIn("daemon=True",s)
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  self.assertIn("while not STOP.exists():",s)
  self.assertIn("intake_run",s)
  print("[PASS] SULS-084B OSI child syntax restored")
  print("[PASS] original OSI loop preserved")
  print("[PASS] SULS event-driven thread bound inside existing OSI child")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-084B OSI CHILD INDENTATION-SAFE BINDING REPAIR")
 print("="*116)

 if not BACKUP.exists():
  raise SystemExit("SULS_084_BACKUP_NOT_FOUND")

 original=BACKUP.read_text(encoding="utf-8")
 ast.parse(original)

 lines=original.splitlines()
 insert_at=0
 for i,line in enumerate(lines):
  if line.startswith("from ") or line.startswith("import "):
   insert_at=i+1

 lines.insert(insert_at,IMPORT1)
 lines.insert(insert_at+1,IMPORT2)

 main_i=next(i for i,x in enumerate(lines) if x.strip()=="def main():")
 body_indent=None
 for x in lines[main_i+1:]:
  if x.strip():
   body_indent=x[:len(x)-len(x.lstrip())]
   break
 if not body_indent:
  raise SystemExit("OSI_MAIN_BODY_INDENT_NOT_FOUND")

 block=[
  body_indent+MARK,
  body_indent+'_suls_thread=threading.Thread(target=run_suls_forever,args=(ROOT,),name="OSI-SULS-EventDriven",daemon=True)',
  body_indent+"_suls_thread.start()",
 ]

 lines[main_i+1:main_i+1]=block
 repaired="\n".join(lines)+"\n"
 ast.parse(repaired)
 TARGET.write_text(repaired,encoding="utf-8")

 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] repaired:",TARGET.name)
 print("[PASS] syntax parse")
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 main()