import subprocess,sys,unittest
class T(unittest.TestCase):
 def test_physical(self):
  p=subprocess.run([sys.executable,"run_oad_290_gmgn_clean_continuous_intelligence_child.py","--max-cycles","1","--cadence-seconds","1"],text=True,capture_output=True,timeout=180);print(p.stdout,end="");print(p.stderr,end="");self.assertEqual(p.returncode,0);self.assertIn("status=SUCCESS",p.stdout);self.assertIn("exact_readback=3",p.stdout)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));raise SystemExit(0 if r.wasSuccessful() else 1)
