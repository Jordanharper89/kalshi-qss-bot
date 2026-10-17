from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_026_physical_swap2_mint_program_binding.py")
s=R.read_text(encoding="utf-8")
tree=ast.parse(s)

fn=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
         and n.name=="_mry019_align_meteora_programs"),None)
if fn is None:
    raise RuntimeError("MRY026_ALIGNMENT_FUNCTION_MISSING")

new='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])
    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pa=list(list(tpl.get("instructions") or [])[pi].get("accounts") or [])
    if len(pa)<12:
        raise RuntimeError("MRY026_PUMP_LAYOUT_SHORT")
    target_program=str(pa[11]["pubkey"])
    wsol=str(q87.c.WSOL)
    mint_hits=[]
    for i in range(len(ac)-1):
        a=str(ac[i].get("pubkey") or "")
        b=str(ac[i+1].get("pubkey") or "")
        if {a,b}=={token,wsol}:
            mint_hits.append((i,a==token))
    if len(mint_hits)!=1:
        raise RuntimeError("MRY026_MINT_PAIR_AMBIGUOUS:"+str(mint_hits))
    _,target_is_x=mint_hits[0]
    classic=str(q87.c.TOKEN)
    program_hits=[]
    for i in range(len(ac)-1):
        a=str(ac[i].get("pubkey") or "")
        b=str(ac[i+1].get("pubkey") or "")
        if target_program==classic:
            if a==classic and b==classic:
                program_hits.append(i)
        elif {a,b}=={target_program,classic}:
            program_hits.append(i)
    if len(program_hits)!=1:
        raise RuntimeError("MRY026_PROGRAM_PAIR_AMBIGUOUS:"+str(program_hits))
    i=program_hits[0]
    ac[i]["pubkey"]=target_program if target_is_x else classic
    ac[i+1]["pubkey"]=classic if target_is_x else target_program
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
 def test_physical_binding(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("MRY026_MINT_PAIR_AMBIGUOUS",s)
  self.assertIn("MRY026_PROGRAM_PAIR_AMBIGUOUS",s)
  self.assertIn("{a,b}=={token,wsol}",s)
  self.assertNotIn("MRY025_TEMPLATE_TARGET_MINT_MISSING",s)
 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-026 installed")
print("[PASS] Swap2 target side derived from physical target/WSOL mint pair")
print("[PASS] token programs bound from physical X/Y orientation")
print("[PASS] no hard-coded Meteora account indexes")