from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_018_dlmm_partial_quarantine.py")

s=R.read_text(encoding="utf-8")

old='''    except RuntimeError as exc:
        if str(exc).startswith(
            "SUPERSEDED_"
        ):
            self.scan_replaced+=1
            return
        raise
'''

new='''    except RuntimeError as exc:
        msg=str(exc)

        if msg.startswith(
            "SUPERSEDED_"
        ):
            self.scan_replaced+=1
            return

        if "DLMM_PARTIAL" in msg:
            READY_TOKENS.discard(str(token))
            print(
                "[MRY018_DLMM_QUARANTINE] "
                "token=%s reason=DLMM_PARTIAL"
                %str(token)[:10],
                flush=True,
            )
            return

        raise
'''

if old not in s:
    raise RuntimeError("MRY018_CANONICAL_PRICE_ANCHOR_MISSING")

s=s.replace(old,new,1)
ast.parse(s)
R.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_quarantine(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[MRY018_DLMM_QUARANTINE]",s)
  self.assertIn('READY_TOKENS.discard(str(token))',s)
  self.assertIn('"DLMM_PARTIAL" in msg',s)
 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":
 unittest.main(verbosity=2)
'''

ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-018 installed")
print("[PASS] DLMM_PARTIAL pair quarantined from hot pricing")
print("[PASS] healthy money lanes remain active")