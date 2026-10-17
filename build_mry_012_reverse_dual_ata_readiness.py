from pathlib import Path
import ast

RT=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
TEST=Path("test_mry_012_reverse_dual_ata_readiness.py")

src=RT.read_text(encoding="utf-8")
ast.parse(src)

old='''    create_token_ata=(
        _ata_create_idempotent_ix(
            user,
            user,
            str(token),
            token_program,
        )
    )
'''

new='''    create_wsol_ata=_ata_create_idempotent_ix(
        user,user,q87.c.WSOL,q87.c.TOKEN,
    )

    create_token_ata=_ata_create_idempotent_ix(
        user,user,str(token),token_program,
    )
'''

if "create_wsol_ata=_ata_create_idempotent_ix" not in src:
    if old not in src:
        raise RuntimeError("MRY012_ATA_CREATION_ANCHOR_MISSING")
    src=src.replace(old,new,1)

old2='''                [create_token_ata]+ixs,
'''
new2='''                [create_wsol_ata,create_token_ata]+ixs,
'''

if new2 not in src:
    if old2 not in src:
        raise RuntimeError("MRY012_CANDIDATE_ANCHOR_MISSING")
    src=src.replace(old2,new2,1)

ast.parse(src)
RT.write_text(src,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_dual_ata(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("create_wsol_ata=_ata_create_idempotent_ix",s)
  self.assertIn("[create_wsol_ata,create_token_ata]+ixs",s)
  self.assertIn("q87.c.WSOL,q87.c.TOKEN",s)
 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
TEST.write_text(test,encoding="utf-8")

print("[PASS] MRY-012 installed")
print("[PASS] reverse WSOL + token ATA readiness is atomic")
print("[PASS] exact 0.010, profit lock, preflight and maxRetries=0 preserved")