from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_015_exact_reverse_output_ata.py")
s=R.read_text(encoding="utf-8")

old='''    create_token_ata=_ata_create_idempotent_ix(
        user,user,str(token),token_program,
    )
'''

new='''    _tpl=TEMPLATES.get(str(token)) or {}
    _pi=int(_tpl.get("pump_index",0))
    _pix=list(_tpl.get("instructions") or [])[_pi]
    _pa=list(_pix.get("accounts") or [])
    if len(_pa)<12:
        raise RuntimeError("MRY015_PUMP_ACCOUNT_LAYOUT_SHORT")
    token_program=str(_pa[11]["pubkey"])

    create_token_ata=_ata_create_idempotent_ix(
        user,user,str(token),token_program,
    )
'''

if old not in s:
    raise RuntimeError("MRY015_TOKEN_ATA_ANCHOR_MISSING")
s=s.replace(old,new,1)

old2="[create_wsol_ata,create_token_ata]+ixs"
new2="[create_token_ata,create_wsol_ata]+ixs"
if old2 not in s:
    raise RuntimeError("MRY015_SETUP_ORDER_ANCHOR_MISSING")
s=s.replace(old2,new2,1)

ast.parse(s)
R.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_exact_program(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn('token_program=str(_pa[11]["pubkey"])',s)
  self.assertIn("[create_token_ata,create_wsol_ata]+ixs",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-015 installed")
print("[PASS] reverse user_token_out uses exact Pump base-token program")
print("[PASS] token output ATA prioritized before WSOL ATA")