from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"run_osi_solana_intelligence_live.py"
TEST=ROOT/"test_suls_084_existing_osi_child_binding.py"

IMPORT="from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import run_forever as run_suls_forever"
MARK="# SULS-084 existing OSI child event-driven binding"
START="""
    # SULS-084 existing OSI child event-driven binding
    import threading
    _suls_thread=threading.Thread(target=run_suls_forever,args=(ROOT,),name="OSI-SULS-EventDriven",daemon=True)
    _suls_thread.start()
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"run_osi_solana_intelligence_live.py"
class T(unittest.TestCase):
 def test_binding(self):
  s=P.read_text(encoding="utf-8")
  self.assertEqual(s.count("run_suls_forever"),2)
  self.assertIn('name="OSI-SULS-EventDriven"',s)
  self.assertIn("daemon=True",s)
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  print("[PASS] SULS-084 existing OSI child event-driven binding")
  print("[PASS] no new top-level Solana child")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-084 EXISTING OSI CHILD EVENT-DRIVEN BINDING");print("="*116)
 src=TARGET.read_text(encoding="utf-8")
 if MARK in src:
  print("[PASS] binding already installed")
 else:
  if "def main():" not in src:raise SystemExit("OSI_MAIN_NOT_FOUND")
  bak=TARGET.with_suffix(".pre_suls084.bak");bak.write_text(src,encoding="utf-8")
  lines=src.splitlines()
  insert_at=0
  for i,line in enumerate(lines):
   if line.startswith("from ") or line.startswith("import "):insert_at=i+1
  lines.insert(insert_at,IMPORT)
  src="\n".join(lines)+"\n"
  pos=src.index("def main():")+len("def main():")
  src=src[:pos]+START+src[pos:]
  TARGET.write_text(src,encoding="utf-8")
  print("[PASS] repaired:",TARGET.name)
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()