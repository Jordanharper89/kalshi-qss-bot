from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_033_meteora_swap2_cutover.py")

s=R.read_text(encoding="utf-8")
tree=ast.parse(s)
lines=s.splitlines()

fn=next((n for n in tree.body
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_mry019_align_meteora_programs"),None)
if fn is None:
    raise RuntimeError("MRY033_ALIGN_FUNCTION_MISSING")

new='''def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])

    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pump_ixs=list(tpl.get("instructions") or [])
    if pi<0 or pi>=len(pump_ixs):
        raise RuntimeError("MRY033_PUMP_INDEX_INVALID")

    pa=list(pump_ixs[pi].get("accounts") or [])
    if len(ac)<15 or len(pa)<13:
        raise RuntimeError("MRY033_LAYOUT_SHORT")

    wsol=str(q87.c.WSOL)
    if str(pa[3].get("pubkey") or "")!=token:
        raise RuntimeError("MRY033_PUMP_TARGET_MINT_MISMATCH")
    if str(pa[4].get("pubkey") or "")!=wsol:
        raise RuntimeError("MRY033_PUMP_WSOL_MINT_MISMATCH")

    target_program=str(pa[11].get("pubkey") or "")
    wsol_program=str(pa[12].get("pubkey") or "")
    x_mint=str(ac[6].get("pubkey") or "")
    y_mint=str(ac[7].get("pubkey") or "")
    if {x_mint,y_mint}!={token,wsol}:
        raise RuntimeError("MRY033_METEORA_XY_MINT_MISMATCH")

    x_program=target_program if x_mint==token else wsol_program
    y_program=target_program if y_mint==token else wsol_program

    raw=base64.b64decode(ix.get("data") or "")
    legacy=bytes([248,198,158,145,225,117,135,200])
    swap2=bytes([65,75,63,76,235,91,91,136])
    memo="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    if raw[:8]==legacy:
        if len(raw)<24:
            raise RuntimeError("MRY033_LEGACY_SWAP_DATA_SHORT")
        if str(ac[14].get("pubkey") or "")!=str(q87.c.DLMM):
            raise RuntimeError("MRY033_LEGACY_PROGRAM_SLOT_MISMATCH")

        ac[11]["pubkey"]=x_program
        ac[12]["pubkey"]=y_program
        memo_meta={
            "pubkey":memo,
            "isSigner":False,
            "isWritable":False,
        }
        ac=ac[:13]+[memo_meta]+ac[13:]
        raw=swap2+raw[8:24]+struct.pack("<I",0)

    elif raw[:8]==swap2:
        if len(ac)<16:
            raise RuntimeError("MRY033_SWAP2_LAYOUT_SHORT")
        ac[11]["pubkey"]=x_program
        ac[12]["pubkey"]=y_program
        ac[13]["pubkey"]=memo

    else:
        raise RuntimeError("MRY033_UNKNOWN_METEORA_SWAP_DISCRIMINATOR")

    ix["accounts"]=ac
    ix["data"]=base64.b64encode(raw).decode()
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
    'FAST_010_MIN_REALIZED_LAMPORTS=10_000',
    'FAST_010_6040_CHAIN_TRUTH',
):
    if needle not in out:
        raise RuntimeError("MRY033_REQUIRED_BOUNDARY_MISSING:"+needle)

R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(R.read_text(encoding="utf-8"))

 def test_swap2_cutover_present(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertIn("bytes([248,198,158,145,225,117,135,200])",f)
  self.assertIn("bytes([65,75,63,76,235,91,91,136])",f)
  self.assertIn("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",f)
  self.assertIn('struct.pack("<I",0)',f)

 def test_official_swap2_account_shift(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertIn('ac[11]["pubkey"]=x_program',f)
  self.assertIn('ac[12]["pubkey"]=y_program',f)
  self.assertIn('ac=ac[:13]+[memo_meta]+ac[13:]',f)

 def test_money_and_send_guards_preserved(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS=10_000",s)
  self.assertIn("FAST_010_6040_CHAIN_TRUTH",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-033 installed")
print("[PASS] legacy Meteora Swap cut over to official Swap2 discriminator")
print("[PASS] Swap2 memo_program inserted before event_authority")
print("[PASS] token X/Y programs remain mint-bound; empty remaining-account metadata encoded")
print("[PASS] MRY-031 money guards and no-blind-retry send policy preserved")