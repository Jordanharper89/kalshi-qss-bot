import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  r=subprocess.run([sys.executable,str(ROOT/"run_solana_scanner_live.py"),"--dry-run"],
   cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout)
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("EVALUATE_TARGET",r.stdout)
  self.assertIn("TARGETED PUMP_SWAP STRATEGY HUNT",r.stdout)
  print("[PASS] SSR-035 targeted rule live runtime cutover")
if __name__=="__main__":unittest.main()
