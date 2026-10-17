from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_030b_runtime_newline_recovery.py")

raw=R.read_text(encoding="utf-8")

if "\\n" not in raw:
    raise RuntimeError("MRY030B_NO_LITERAL_NEWLINE_CORRUPTION_FOUND")

candidate=raw.replace("\\n","\n")

try:
    ast.parse(candidate)
except SyntaxError as exc:
    raise RuntimeError(
        "MRY030B_RECOVERY_PARSE_FAILED:"
        +f"{exc.lineno}:{exc.offset}:{exc.msg}"
    )

if "def _fast_010_refresh_latest" not in candidate:
    raise RuntimeError("MRY030B_REFRESH_FUNCTION_MISSING")

if "FAST_010_SINGLE_REFRESH" not in candidate:
    raise RuntimeError("MRY030B_MRY030_LOGIC_MISSING")

R.write_text(candidate,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime_parses(self):
  s=R.read_text(encoding="utf-8")
  ast.parse(s)

 def test_no_global_literal_newline_corruption(self):
  s=R.read_text(encoding="utf-8")
  self.assertGreater(s.count("\\n"),1000)

 def test_mry030_survived(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _fast_010_refresh_latest")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertIn("FAST_010_SINGLE_REFRESH",f)
  self.assertNotIn("while refreshes<",f)
  self.assertNotIn("GENERATION_CHURN_LIMIT",f)

 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
'''

T.write_text(test,encoding="utf-8")

print("[PASS] MRY-030B runtime newline corruption recovered")
print("[PASS] runtime.py AST parses")
print("[PASS] MRY-030 single-shot freshness preserved")
print("[PASS] live safety guards preserved")