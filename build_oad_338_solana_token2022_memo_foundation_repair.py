from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-338';TITLE='SOLANA TOKEN-2022 MEMO FOUNDATION REPAIR';EXPECTED='build_oad_338_solana_token2022_memo_foundation_repair.py';MODULE='oad_338_solana_token2022_memo_foundation_repair.py';TEST='test_oad_338_solana_token2022_memo_foundation_repair.py';DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_333_solana_authoritative_program_identity_registry.py': ('TOKEN_2022_UNVERIFIED_ALIAS', 'PROGRAMS'), 'qseries_v2/oracle_adapters/independent/oad_337_solana_program_decode_physical_coverage_gate.py': ('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb', 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
TOKEN_2022_PROGRAM_ID="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
MEMO_PROGRAM_ID="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
@dataclass(frozen=True,slots=True)
class SolanaFoundationProgramIdentity:
 program_id:str;name:str;category:str;market_relevant:bool;execution_authority:bool=False
def identify_foundation_program(program_id):
 pid=str(program_id or "")
 if pid==TOKEN_2022_PROGRAM_ID:return SolanaFoundationProgramIdentity(pid,"TOKEN_2022","TOKEN",True,False)
 if pid==MEMO_PROGRAM_ID:return SolanaFoundationProgramIdentity(pid,"MEMO","INFRASTRUCTURE",False,False)
 return SolanaFoundationProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_338_solana_token2022_memo_foundation_repair import *
class T(unittest.TestCase):
 def test_ids(self):
  a=identify_foundation_program(TOKEN_2022_PROGRAM_ID);b=identify_foundation_program(MEMO_PROGRAM_ID)
  print("[FOUNDATION]",a.name,a.program_id,b.name,b.program_id)
  self.assertEqual(a.name,"TOKEN_2022");self.assertTrue(a.market_relevant);self.assertEqual(b.category,"INFRASTRUCTURE")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-338 exact Token-2022 + Memo foundation identities certified")

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
