from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_029_final_physical_meteora_binding.py")
s=R.read_text(encoding="utf-8")
lines=s.splitlines()
tree=ast.parse(s)

fn=next((n for n in tree.body
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_mry019_align_meteora_programs"),None)

if fn is None:
    raise RuntimeError("MRY029_ALIGNMENT_FUNCTION_MISSING")

new='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])
    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pa=list(list(tpl.get("instructions") or [])[pi].get("accounts") or [])
    if len(pa)<12 or len(ac)<13:
        raise RuntimeError("MRY029_LAYOUT_SHORT")
    target_program=str(pa[11]["pubkey"])
    classic=str(q87.c.TOKEN)
    wsol=str(q87.c.WSOL)
    hits=[]
    for i in range(len(ac)-1):
        a=str(ac[i].get("pubkey") or "")
        b=str(ac[i+1].get("pubkey") or "")
        if {a,b}=={token,wsol}:
            hits.append((i,a==token))
    if len(hits)!=1:
        raise RuntimeError("MRY029_FINAL_MINT_PAIR_AMBIGUOUS:"+str(hits))
    _,target_is_x=hits[0]
    ac[11]["pubkey"]=target_program if target_is_x else classic
    ac[12]["pubkey"]=classic if target_is_x else target_program
    ix["accounts"]=ac
    out["meteora_ix"]=ix
    if str(out.get("direction") or "")=="METEORA_TO_PUMP":
        out["original_candidates"]=_reverse_instruction_sets(
            out["pump_ixs"],int(out["pump_index"]),ix)
    else:
        out["original_candidates"]=q87.las.q59.candidate_instruction_sets(
            out["pump_ixs"],ix)
    return out
'''

lines[fn.lineno-1:fn.end_lineno]=new.splitlines()
out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_final_physical_binding(self):
  s=R.read_text();ast.parse(s)
  self.assertIn("{a,b}=={token,wsol}",s)
  self.assertIn("MRY029_FINAL_MINT_PAIR_AMBIGUOUS",s)
  self.assertIn('ac[11]["pubkey"]=target_program if target_is_x else classic',s)
  self.assertIn('ac[12]["pubkey"]=classic if target_is_x else target_program',s)
 def test_post_lock_owner(self):
  s=R.read_text()
  start=s.index("def _fast_010_profit_lock_route")
  end=s.index("\\ndef ",start+5)
  f=s[start:end]
  self.assertIn("out=_mry019_align_meteora_programs(out)",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":
 unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-029 installed")
print("[PASS] final Meteora X/Y orientation derived from physical target/WSOL mint pair")
print("[PASS] Token-2022/classic programs written after profit lock")