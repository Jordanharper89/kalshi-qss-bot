import ast,unittest
from pathlib import Path
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
RT=PKG/"runtime.py"
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=RT.read_text(encoding="utf-8");cls.tree=ast.parse(cls.src)
    def test_imports(self):
        self.assertIn("mry_005_runtime_activation",self.src)
        self.assertIn("mry_002_warm_inventory",self.src)
    def test_warm_40_before_prepare(self):
        run=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=="run")
        s=ast.get_source_segment(self.src,run) or ""
        self.assertIn("configure_hydration(40)",s)
        self.assertLess(s.index("configure_hydration(40)"),s.index("q25.prepare_once"))
    def test_rotating_serve(self):
        self.assertIn("mry5.serve_rotating(",self.src)
    def test_money_path_preserved(self):
        for x in ("_live_010_certify_or_send","CANARY_TRADE_LAMPORTS=10_000_000",'"skipPreflight":False','"maxRetries":0'):
            self.assertIn(x,self.src)
if __name__=="__main__":unittest.main(verbosity=2)
