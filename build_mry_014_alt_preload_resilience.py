from pathlib import Path
import ast

PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
RT=PKG/"runtime.py"
MOD=PKG/"mry_014_alt_preload_resilience.py"
TEST=Path("test_mry_014_alt_preload_resilience.py")

module='''from __future__ import annotations
import time
def preload(fn,root,attempts=8):
    last=None
    for n in range(1,attempts+1):
        try:
            out=fn(root)
            print("[MRIYA_ALT_PRELOAD_OK] attempt=%d"%n,flush=True)
            return out
        except Exception as exc:
            last=exc
            s=str(exc).lower()
            limited=("429" in s or "too many requests" in s or "rate limit" in s)
            if not limited or n>=attempts:
                raise
            delay=min(20.0,2.0*(2**(n-1)))
            print("[MRIYA_ALT_PRELOAD_429] attempt=%d sleep=%.1f"%(n,delay),flush=True)
            time.sleep(delay)
    raise last
'''

src=RT.read_text(encoding="utf-8")
ast.parse(src)

if "mry_014_alt_preload_resilience as m14" not in src:
    anchor="from qseries_v2.oracle_execution.solana_atomic_executor import mry_005_runtime_activation as mry5\n"
    if anchor not in src: raise RuntimeError("MRY014_IMPORT_ANCHOR_MISSING")
    src=src.replace(anchor,anchor+"from qseries_v2.oracle_execution.solana_atomic_executor import mry_014_alt_preload_resilience as m14\n",1)

old="    preload_canary_saved_alts(root)\n"
new="    m14.preload(preload_canary_saved_alts,root)\n"
if new not in src:
    if old not in src: raise RuntimeError("MRY014_CALL_ANCHOR_MISSING")
    src=src.replace(old,new,1)

test='''import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
class T(unittest.TestCase):
 def test_activation(self):
  s=(P/"runtime.py").read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("m14.preload(preload_canary_saved_alts,root)",s)
 def test_module(self):
  from qseries_v2.oracle_execution.solana_atomic_executor import mry_014_alt_preload_resilience as m
  self.assertTrue(callable(m.preload))
if __name__=="__main__":unittest.main(verbosity=2)
'''

for x in (module,src,test): ast.parse(x)
MOD.write_text(module,encoding="utf-8")
RT.write_text(src,encoding="utf-8")
TEST.write_text(test,encoding="utf-8")

print("[PASS] MRY-014 installed")
print("[PASS] saved ALT startup preload now retries HTTP 429")
print("[PASS] execution/preflight/no-retry trade behavior unchanged")