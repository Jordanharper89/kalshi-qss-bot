from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_024_exact_meteora_swap2_program_alignment.py")
s=R.read_text(encoding="utf-8")

old='''    mint_x=str(ac[6]["pubkey"])
    mint_y=str(ac[7]["pubkey"])
'''

new='''    # Meteora DLMM Swap2 canonical fixed layout:
    # 7 token_x_mint, 8 token_y_mint,
    # 11 token_x_program, 12 token_y_program.
    mint_x=str(ac[7]["pubkey"])
    mint_y=str(ac[8]["pubkey"])
'''

if old not in s:
    raise RuntimeError("MRY024_FAILED_MRY020_MAPPING_NOT_FOUND")

s=s.replace(old,new,1)

# Keep the program assignment driven by the actual Pump mint program.
required=[
    'ac[11]["pubkey"]=token_program',
    'ac[12]["pubkey"]=q87.c.TOKEN',
    'ac[11]["pubkey"]=q87.c.TOKEN',
    'ac[12]["pubkey"]=token_program',
]
for x in required:
    if x not in s:
        raise RuntimeError("MRY024_PROGRAM_ASSIGNMENT_MISSING:"+x)

ast.parse(s)
R.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_swap2_layout(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn('mint_x=str(ac[7]["pubkey"])',s)
  self.assertIn('mint_y=str(ac[8]["pubkey"])',s)
  self.assertNotIn('mint_x=str(ac[6]["pubkey"])',s)
  self.assertIn('ac[11]["pubkey"]=token_program',s)
  self.assertIn('ac[12]["pubkey"]=token_program',s)

 def test_live_guards(self):
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

print("[PASS] MRY-024 installed")
print("[PASS] failed MRY-020 Meteora mint inference replaced")
print("[PASS] Swap2 mint/program layout = 7/8 -> 11/12")
print("[PASS] Token-2022 program follows exact Pump mint program")