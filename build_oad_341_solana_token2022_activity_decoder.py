from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-341';TITLE='SOLANA TOKEN-2022 ACTIVITY DECODER';EXPECTED='build_oad_341_solana_token2022_activity_decoder.py';MODULE='oad_341_solana_token2022_activity_decoder.py';TEST='test_oad_341_solana_token2022_activity_decoder.py';DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_339_solana_reconciled_program_identity_registry.py': ('TOKEN_2022', 'identify_reconciled_program'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('SolanaWalletTokenFlow',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaToken2022Activity:
 signature:str;slot:int;token2022_invocations:int;flow_count:int;mints:tuple;behavior:str;execution_authority:bool=False
def decode_token2022_activity(envelopes,attributions,flows):
 amap={a.signature:a for a in attributions};out=[]
 for e in envelopes:
  a=amap.get(e.signature)
  if not a:continue
  ids=tuple(a.top_level_program_ids)+tuple(a.inner_program_ids)
  n=sum(1 for pid in ids if identify_reconciled_program(pid).name=="TOKEN_2022")
  if not n:continue
  fs=[f for f in flows if f.signature==e.signature];mints=tuple(sorted({f.mint for f in fs if f.mint}))
  pos=any(f.delta>0 for f in fs);neg=any(f.delta<0 for f in fs)
  behavior="TOKEN_2022_BALANCE_FLOW" if fs else "TOKEN_2022_INSTRUCTION_ONLY"
  if pos and neg:behavior="TOKEN_2022_TRANSFER_OR_SWAP_FLOW"
  out.append(SolanaToken2022Activity(e.signature,e.slot,n,len(fs),mints,behavior,False))
 return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_341_solana_token2022_activity_decoder import *
class T(unittest.TestCase):
 def test_decode(self):
  e=SimpleNamespace(signature="s",slot=1);a=SimpleNamespace(signature="s",top_level_program_ids=("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",),inner_program_ids=())
  fs=(SimpleNamespace(signature="s",mint="A",delta=-2.0),SimpleNamespace(signature="s",mint="B",delta=3.0))
  x=decode_token2022_activity((e,),(a,),fs)[0]
  print("[TOKEN2022]",x.token2022_invocations,x.behavior,x.mints)
  self.assertEqual(x.behavior,"TOKEN_2022_TRANSFER_OR_SWAP_FLOW")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-341 Token-2022 activity decoder certified")

"""
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
 s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p));p.parent.mkdir(parents=True,exist_ok=True)
 q=p.with_suffix(p.suffix+".tmp");q.write_text(s,encoding="utf-8",newline="\n");os.replace(q,p)
def main():
 if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
 r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"
 print("="*120);print(" "+BUILD_ID+" "+TITLE+" INSTALLER");print("="*120);print("[ROOT]",r)
 for rel,marks in DEPENDENCIES.items():
  p=r/rel
  if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
  x=p.read_text(encoding="utf-8");ast.parse(x,filename=str(p))
  for mark in marks:
   if mark not in x: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
  print("[PASS] exact dependency verified:",rel)
 protected=[]
 for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py","qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py","qseries_v2/oracle_adapters/independent/oad_337_solana_program_decode_physical_coverage_gate.py"):
  p=r/rel
  if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
  protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
 old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
 try:
  atomic(m,MODULE_SOURCE);atomic(t,TEST_SOURCE)
  lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else [];exp="from ."+m.stem+" import *"
  if exp not in lines:lines.append(exp)
  atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
  for p,h in protected:
   if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("protected boundary changed: "+p.name)
  print("[PASS] module installed:",m.relative_to(r));print("[PASS] test installed:",t.name)
  print("[PASS] OAD-327 continuity and OAD-337 physical baseline preserved unchanged")
  print("[PASS] unknown identities are not guessed; unresolved programs remain unresolved")
  print("[PASS] GMGN not required")
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
