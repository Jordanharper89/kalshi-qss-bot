from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_032_exact_meteora_xy_program_binding.py")

s=R.read_text(encoding="utf-8")
tree=ast.parse(s)
lines=s.splitlines()

fn=next((n for n in tree.body
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_mry019_align_meteora_programs"),None)
if fn is None:
    raise RuntimeError("MRY032_ALIGN_FUNCTION_MISSING")

new='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])

    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pump_ixs=list(tpl.get("instructions") or [])

    if pi<0 or pi>=len(pump_ixs):
        raise RuntimeError("MRY032_PUMP_INDEX_INVALID")

    pa=list(pump_ixs[pi].get("accounts") or [])
    if len(ac)<13 or len(pa)<13:
        raise RuntimeError("MRY032_LAYOUT_SHORT")

    wsol=str(q87.c.WSOL)

    if str(pa[3].get("pubkey") or "")!=token:
        raise RuntimeError("MRY032_PUMP_TARGET_MINT_MISMATCH")
    if str(pa[4].get("pubkey") or "")!=wsol:
        raise RuntimeError("MRY032_PUMP_WSOL_MINT_MISMATCH")

    target_program=str(pa[11].get("pubkey") or "")
    wsol_program=str(pa[12].get("pubkey") or "")
    if not target_program or not wsol_program:
        raise RuntimeError("MRY032_PUMP_PROGRAM_MISSING")

    x_mint=str(ac[6].get("pubkey") or "")
    y_mint=str(ac[7].get("pubkey") or "")

    if {x_mint,y_mint}!={token,wsol}:
        raise RuntimeError(
            "MRY032_METEORA_XY_MINT_MISMATCH:"
            +str((x_mint,y_mint,token,wsol))
        )

    x_program=target_program if x_mint==token else wsol_program
    y_program=target_program if y_mint==token else wsol_program

    ac[11]["pubkey"]=x_program
    ac[12]["pubkey"]=y_program
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

for needle in (
    '"skipPreflight":False',
    '"maxRetries":0',
    'CANARY_TRADE_LAMPORTS=10_000_000',
    'def fast_live_attack',
    'FAST_010_6040_CHAIN_TRUTH',
):
    if needle not in out:
        raise RuntimeError("MRY032_REQUIRED_BOUNDARY_MISSING:"+needle)

R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(R.read_text(encoding="utf-8"))

 def test_exact_xy_slots(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertIn('x_mint=str(ac[6].get("pubkey") or "")',f)
  self.assertIn('y_mint=str(ac[7].get("pubkey") or "")',f)
  self.assertIn('ac[11]["pubkey"]=x_program',f)
  self.assertIn('ac[12]["pubkey"]=y_program',f)
  self.assertNotIn("hits=[]",f)
  self.assertNotIn("target_is_x",f)

 def test_program_source_is_physical_pump_layout(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertIn('pa[3].get("pubkey")',f)
  self.assertIn('pa[4].get("pubkey")',f)
  self.assertIn('pa[11].get("pubkey")',f)
  self.assertIn('pa[12].get("pubkey")',f)

 def test_money_guards_preserved(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn("FAST_010_6040_CHAIN_TRUTH",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-032 installed")
print("[PASS] Meteora token_x_program bound from actual token_x_mint slot")
print("[PASS] Meteora token_y_program bound from actual token_y_mint slot")
print("[PASS] adjacency inference removed; MRY-031 money guards preserved")
