import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
class T(unittest.TestCase):
    def test_runtime_preloader(self):
        s=(P/"runtime.py").read_text(encoding="utf-8");self.assertIn("REVERSE_005_PRELOAD",s);ast.parse(s)
    def test_admission_refresh(self):
        s=(P/"mry_010_live_promotion.py").read_text(encoding="utf-8");self.assertIn("rev.refresh(rt,state,root)",s);ast.parse(s)
if __name__=="__main__":unittest.main(verbosity=2)
