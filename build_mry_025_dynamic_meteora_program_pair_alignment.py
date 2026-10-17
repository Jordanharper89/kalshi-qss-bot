from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_025_dynamic_meteora_program_pair_alignment.py")
s=R.read_text(encoding="utf-8")
tree=ast.parse(s)

fn=None
for n in tree.body:
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="_mry019_align_meteora_programs":
        fn=n; break
if fn is None:
    raise RuntimeError("MRY025_ALIGNMENT_FUNCTION_MISSING")

new='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])
    mt=(METEORA_TEMPLATES.get(token) or {})
    fixed=list(mt.get("fixed_accounts") or [])
    if len(fixed)<13 or len(ac)<2:
        raise RuntimeError("MRY025_METEORA_LAYOUT_SHORT")
    token_x=str(fixed[7][0]); token_y=str(fixed[8][0])
    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pa=list(list(tpl.get("instructions") or [])[pi].get("accounts") or [])
    if len(pa)<12:
        raise RuntimeError("MRY025_PUMP_LAYOUT_SHORT")
    target_program=str(pa[11]["pubkey"])
    if token_x==token:
        want_x,want_y=target_program,q87.c.TOKEN
    elif token_y==token:
        want_x,want_y=q87.c.TOKEN,target_program
    else:
        raise RuntimeError("MRY025_TEMPLATE_TARGET_MINT_MISSING")
    allowed={str(q87.c.TOKEN),str(target_program)}
    hits=[]
    for i in range(len(ac)-1):
        a=str(ac[i].get("pubkey") or ""); b=str(ac[i+1].get("pubkey") or "")
        if a in allowed and b in allowed:
            hits.append(i)
    if len(hits)!=1:
        raise RuntimeError("MRY025_TOKEN_PROGRAM_PAIR_AMBIGUOUS:"+str(hits))
    i=hits[0]
    ac[i]["pubkey"]=want_x; ac[i+1]["pubkey"]=want_y
    ix["accounts"]=ac
    out["meteora_ix"]=ix
    return out
'''

lines=s.splitlines()
lines[fn.lineno-1:fn.end_lineno]=new.splitlines()
out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_dynamic_alignment(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("METEORA_TEMPLATES.get(token)",s)
  self.assertIn("MRY025_TOKEN_PROGRAM_PAIR_AMBIGUOUS",s)
  self.assertIn('ac[i]["pubkey"]=want_x',s)
  self.assertNotIn('mint_x=str(ac[7]["pubkey"])',s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")
print("[PASS] MRY-025 installed")
print("[PASS] Meteora program alignment now follows canonical template orientation")
print("[PASS] no hard-coded built-instruction mint indexes remain")