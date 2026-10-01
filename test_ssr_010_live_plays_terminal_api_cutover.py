import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  p=ROOT/"run_solana_scanner_live.py";self.assertTrue(p.exists())
  r=subprocess.run([sys.executable,str(p),"--dry-run"],cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("LIVE PLAYS",r.stdout);self.assertIn("READY=",r.stdout);self.assertIn("OBSERVE=",r.stdout)
  self.assertIn("execution_authority=FALSE",r.stdout)
  print("[PASS] SSR-010 live plays terminal + /plays API cutover")
  print("[RUN] python run_solana_scanner_live.py")
if __name__=="__main__":unittest.main()
