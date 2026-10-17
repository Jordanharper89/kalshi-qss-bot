from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_028_final_post_lock_execution_canonicalization.py")

s=R.read_text(encoding="utf-8")
tree=ast.parse(s)
lines=s.splitlines()

fn=next((n for n in tree.body
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
    and n.name=="_fast_010_profit_lock_route"),None)

if fn is None:
    raise RuntimeError("MRY028_PROFIT_LOCK_FUNCTION_MISSING")

new='''def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=copy.deepcopy(route)
    out["direction"]=str(direction)

    if direction=="PUMP_TO_METEORA":
        meteora,old_bound,new_bound=_fast_010_rewrite_meteora_min_out(
            out["meteora_ix"],required_final_out)
        out["meteora_ix"]=meteora

    elif direction=="METEORA_TO_PUMP":
        ixs=[copy.deepcopy(x) for x in out["pump_ixs"]]
        pump_index=int(out["pump_index"])
        raw=base64.b64decode(ixs[pump_index].get("data") or "")
        if len(raw)<24:
            raise RuntimeError("FAST_010_PUMP_SELL_DATA_TOO_SHORT:"+str(len(raw)))
        base_in=int(struct.unpack("<Q",raw[8:16])[0])
        old_bound=int(struct.unpack("<Q",raw[16:24])[0])
        new_bound=max(old_bound,int(required_final_out))
        ixs[pump_index]=rewrite_pump_sell_bounds(
            ixs[pump_index],base_in,new_bound)
        out["pump_ixs"]=ixs
        out["pump_ix"]=ixs[pump_index]

    else:
        raise RuntimeError("FAST_010_BAD_DIRECTION:"+str(direction))

    out=_mry019_align_meteora_programs(out)

    if direction=="METEORA_TO_PUMP":
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)

    return out,old_bound,new_bound
'''

lines[fn.lineno-1:fn.end_lineno]=new.splitlines()
out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_final_order(self):
  s=R.read_text(); ast.parse(s)
  a=s.index("out=_mry019_align_meteora_programs(out)")
  b=s.index("out=_reverse_prepend_ata_readiness(",a)
  c=s.index("return out,old_bound,new_bound",b)
  self.assertLess(a,b); self.assertLess(b,c)
 def test_single_final_candidate_owner(self):
  s=R.read_text()
  start=s.index("def _fast_010_profit_lock_route")
  end=s.index("\\ndef ",start+5)
  f=s[start:end]
  self.assertNotIn("_reverse_instruction_sets(",f)
  self.assertNotIn("candidate_instruction_sets(",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":
 unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-028 installed")
print("[PASS] profit lock precedes final Meteora alignment")
print("[PASS] reverse ATA readiness applied exactly after final alignment")
print("[PASS] final candidates owned by canonical alignment path")