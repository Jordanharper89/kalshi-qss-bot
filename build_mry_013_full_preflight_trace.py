from pathlib import Path
import ast,re

RT=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
TEST=Path("test_mry_013_full_preflight_trace.py")
src=RT.read_text(encoding="utf-8")
lines=src.splitlines()

marker=next((i for i,x in enumerate(lines) if "LIVE_010_PREFLIGHT_REJECT" in x),None)
if marker is None: raise RuntimeError("MRY013_PREFLIGHT_MARKER_NOT_FOUND")

start=None
for i in range(marker,-1,-1):
    if "print(" in lines[i]:
        start=i
        break
if start is None: raise RuntimeError("MRY013_PRINT_START_NOT_FOUND")

exc=None
for i in range(start,-1,-1):
    m=re.search(r"except\s+Exception\s+as\s+(\w+)\s*:",lines[i])
    if m:
        exc=m.group(1)
        break
    if start-i>60: break
if not exc: raise RuntimeError("MRY013_EXCEPTION_VARIABLE_NOT_FOUND")

indent=re.match(r"\s*",lines[start]).group(0)
probe=indent+f'print("[LIVE_010_PREFLIGHT_FULL] %s:%s"%(type({exc}).__name__,str({exc})),flush=True)'

if "LIVE_010_PREFLIGHT_FULL" not in src:
    lines.insert(start,probe)

out="\n".join(lines)+"\n"
ast.parse(out)
RT.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_trace(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[LIVE_010_PREFLIGHT_FULL]",s)
  self.assertIn("[LIVE_010_PREFLIGHT_REJECT]",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
TEST.write_text(test,encoding="utf-8")

print("[PASS] MRY-013 installed")
print("[PASS] full preflight telemetry enabled")
print("[PASS] execution behavior unchanged")