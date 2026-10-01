import subprocess,sys,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_005_launcher_contract import contract
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_launcher(self):
  c=contract();p=ROOT/c["launcher"];self.assertTrue(p.exists())
  r=subprocess.run([sys.executable,str(p),"--dry-run"],cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("SOLANA PROFITABILITY SCANNER",r.stdout);self.assertIn("execution_authority",r.stdout);self.assertFalse(c["execution_authority"])
  print("[PASS] SSR-005 standalone Solana profitability runtime launcher")
  print("[RUN] python run_solana_scanner_live.py")
if __name__=="__main__":unittest.main()
