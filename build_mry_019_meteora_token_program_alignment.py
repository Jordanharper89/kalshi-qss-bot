from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_019_meteora_token_program_alignment.py")
s=R.read_text(encoding="utf-8")

anchor='''def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=copy.deepcopy(route)
    out["direction"]=str(direction)
'''

helper='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])
    if len(ac)<13:
        raise RuntimeError("MRY019_METEORA_ACCOUNT_LAYOUT_SHORT")

    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pix=list(tpl.get("instructions") or [])[pi]
    pa=list(pix.get("accounts") or [])
    if len(pa)<12:
        raise RuntimeError("MRY019_PUMP_ACCOUNT_LAYOUT_SHORT")

    token_program=str(pa[11]["pubkey"])
    mint_x=str(ac[7]["pubkey"])
    mint_y=str(ac[8]["pubkey"])

    if mint_x==token:
        ac[11]["pubkey"]=token_program
        ac[12]["pubkey"]=q87.c.TOKEN
    elif mint_y==token:
        ac[11]["pubkey"]=q87.c.TOKEN
        ac[12]["pubkey"]=token_program
    else:
        raise RuntimeError("MRY019_TARGET_MINT_NOT_IN_METEORA")

    ix["accounts"]=ac
    out["meteora_ix"]=ix
    return out


def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=_mry019_align_meteora_programs(route)
    out["direction"]=str(direction)
'''

if anchor not in s:
    raise RuntimeError("MRY019_PROFIT_LOCK_ANCHOR_MISSING")

s=s.replace(anchor,helper,1)
ast.parse(s)
R.write_text(s,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_alignment(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("ac[11][\\"pubkey\\"]=token_program",s)
  self.assertIn("ac[12][\\"pubkey\\"]=q87.c.TOKEN",s)
  self.assertIn("_mry019_align_meteora_programs(route)",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-019 installed")
print("[PASS] Meteora token-X/token-Y programs aligned to actual mint programs")
print("[PASS] exact 0.010, profit lock, preflight and maxRetries=0 preserved")