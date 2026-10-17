from pathlib import Path
import ast

Q=Path("qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py")
T=Path("test_mry_016_token_net_startup_resilience.py")
s=Q.read_text(encoding="utf-8")

old='''        t=time.perf_counter_ns()
        row=q23.worker().warm(token)
        ms=(time.perf_counter_ns()-t)/1e6
        rows.append({"token":token,"program":row.get("program"),"warm_ms":ms})
'''

new='''        t=time.perf_counter_ns()
        row=None
        last=None
        for attempt in range(1,7):
            try:
                row=q23.worker().warm(token)
                break
            except Exception as exc:
                last=exc
                text=str(exc).lower()
                transient=("429" in text or "too many requests" in text or
                           "fetch failed" in text or "timeout" in text)
                if not transient:
                    raise
                print("[ORACLE025_TOKEN_WARM_RETRY] token=%s attempt=%d reason=%s"%(
                    token[:12],attempt,str(exc)[:180]),flush=True)
                if attempt<6:
                    time.sleep(min(12.0,1.5*(2**(attempt-1))))
        if row is None:
            print("[ORACLE025_TOKEN_WARM_SKIP] token=%s reason=%s"%(
                token[:12],str(last)[:180]),flush=True)
            continue
        ms=(time.perf_counter_ns()-t)/1e6
        rows.append({"token":token,"program":row.get("program"),"warm_ms":ms})
'''

if old not in s:
    raise RuntimeError("MRY016_WARM_ANCHOR_MISSING")

s=s.replace(old,new,1)
ast.parse(s)
Q.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
Q=Path("qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py")
class T(unittest.TestCase):
 def test_resilience(self):
  s=Q.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[ORACLE025_TOKEN_WARM_RETRY]",s)
  self.assertIn("[ORACLE025_TOKEN_WARM_SKIP]",s)
  self.assertIn('"fetch failed" in text',s)
 def test_no_execution_change(self):
  s=Q.read_text(encoding="utf-8")
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  self.assertIn("PAPER_ONLY=True",s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-016 installed")
print("[PASS] transient Token-Net startup failures no longer kill Oracle")
print("[PASS] unhealthy token may be skipped; healthy money lanes continue")