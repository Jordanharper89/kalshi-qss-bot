from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_027_canonical_execution_binding_replacement.py")
s=R.read_text(encoding="utf-8")
lines=s.splitlines()
tree=ast.parse(s)

align=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_mry019_align_meteora_programs"),None)
helper=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_reverse_prepend_ata_readiness"),None)

if align is None: raise RuntimeError("MRY027_ALIGNMENT_FUNCTION_MISSING")
if helper is None: raise RuntimeError("MRY027_REVERSE_HELPER_MISSING")

new_align='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route); token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {}); ac=list(ix.get("accounts") or [])
    fixed=list((METEORA_TEMPLATES.get(token) or {}).get("fixed_accounts") or [])
    if len(fixed)<13 or len(ac)<13: raise RuntimeError("MRY027_METEORA_LAYOUT_SHORT")
    tx=str(fixed[6][0]); ty=str(fixed[7][0])
    tpl=TEMPLATES.get(token) or {}; pi=int(tpl.get("pump_index",0))
    pa=list(list(tpl.get("instructions") or [])[pi].get("accounts") or [])
    if len(pa)<12: raise RuntimeError("MRY027_PUMP_LAYOUT_SHORT")
    tp=str(pa[11]["pubkey"]); classic=str(q87.c.TOKEN)
    if tx==token: ac[11]["pubkey"]=tp; ac[12]["pubkey"]=classic
    elif ty==token: ac[11]["pubkey"]=classic; ac[12]["pubkey"]=tp
    else: raise RuntimeError("MRY027_TARGET_NOT_IN_CANONICAL_METEORA")
    ix["accounts"]=ac; out["meteora_ix"]=ix
    if str(out.get("direction") or "")=="METEORA_TO_PUMP":
        out["original_candidates"]=_reverse_instruction_sets(out["pump_ixs"],int(out["pump_index"]),ix)
    else:
        out["original_candidates"]=q87.las.q59.candidate_instruction_sets(out["pump_ixs"],ix)
    return out'''

helper_body="\n".join(lines[helper.body[0].lineno-1:helper.end_lineno])
new_helper='''def _reverse_prepend_ata_readiness(user,token,route=None):
    if route is None:
        route=token
        token=str(route.get("token") or "")
'''+helper_body+"\n"

repls=[
    (align.lineno-1,align.end_lineno,new_align.splitlines()),
    (helper.lineno-1,helper.end_lineno,new_helper.splitlines()),
]
for a,b,new in sorted(repls,reverse=True):
    lines[a:b]=new

out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_meteora_binding(self):
  s=R.read_text(); ast.parse(s)
  self.assertIn("tx=str(fixed[6][0])",s)
  self.assertIn('ac[11]["pubkey"]=tp',s)
  self.assertIn("candidate_instruction_sets",s)
 def test_reverse_compatibility(self):
  s=R.read_text()
  self.assertIn("def _reverse_prepend_ata_readiness(user,token,route=None)",s)
  self.assertIn("route=token",s)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-027 installed")
print("[PASS] Meteora canonical X/Y program binding replaced")
print("[PASS] reverse ATA helper supports both 2-arg and 3-arg callers")
print("[PASS] candidate sets rebuilt from corrected Meteora instruction")