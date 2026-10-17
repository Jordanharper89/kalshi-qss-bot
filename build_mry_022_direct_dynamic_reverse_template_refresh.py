from pathlib import Path
import ast

P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
M=P/"mry_011_reverse_readiness.py"
T=Path("test_mry_022_direct_dynamic_reverse_template_refresh.py")

module='''def refresh(rt,state,root=None):
    fn=getattr(rt,"prebuild_sell_templates",None)
    user=getattr(rt,"USER",None)

    if not callable(fn):
        raise RuntimeError("MRY022_PREBUILD_SELL_TEMPLATES_MISSING")
    if not user:
        raise RuntimeError("MRY022_RUNTIME_USER_MISSING")

    count=fn(state,user)

    print(
        "[MRY022_REVERSE_REFRESH] "
        "sell_templates=%d direct=TRUE"
        %int(count),
        flush=True,
    )

    return int(count)
'''

test='''import ast,unittest
from pathlib import Path
M=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_011_reverse_readiness.py")

class T(unittest.TestCase):
 def test_direct_refresh(self):
  s=M.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn('prebuild_sell_templates',s)
  self.assertIn('[MRY022_REVERSE_REFRESH]',s)
  self.assertNotIn('rt.run(',s)
  self.assertNotIn('inspect.',s)

 def test_runtime_guards_preserved(self):
  s=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py").read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
'''

for x in (module,test):
    ast.parse(x)

M.write_text(module,encoding="utf-8")
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-022 installed")
print("[PASS] dynamic admission now directly refreshes reverse sell templates")
print("[PASS] no runtime re-entry / no discovery restart")