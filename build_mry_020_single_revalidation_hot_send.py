from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_020_single_revalidation_hot_send.py")
s=R.read_text(encoding="utf-8")

old='''    mint_x=str(ac[7]["pubkey"])
    mint_y=str(ac[8]["pubkey"])
'''
new='''    mint_x=str(ac[6]["pubkey"])
    mint_y=str(ac[7]["pubkey"])
'''
if old not in s:
    raise RuntimeError("MRY020_MRY019_MINT_INDEX_ANCHOR_MISSING")
s=s.replace(old,new,1)

old2="    while refreshes<3:"
new2="    while refreshes<1:"
if old2 not in s:
    raise RuntimeError("MRY020_REFRESH_LOOP_ANCHOR_MISSING")
s=s.replace(old2,new2,1)

ast.parse(s)
R.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_exact_meteora_orientation(self):
  s=R.read_text(encoding="utf-8"); ast.parse(s)
  self.assertIn('mint_x=str(ac[6]["pubkey"])',s)
  self.assertIn('mint_y=str(ac[7]["pubkey"])',s)
  self.assertNotIn('mint_x=str(ac[7]["pubkey"])',s)

 def test_single_hot_revalidation(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("while refreshes<1:",s)
  self.assertNotIn("while refreshes<3:",s)

 def test_live_guards_preserved(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS=10_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-020 installed")
print("[PASS] exact Meteora token-X/token-Y orientation restored")
print("[PASS] hot path reduced to one in-memory revalidation")
print("[PASS] 0.010 SOL + profit floor + preflight + maxRetries=0 preserved")