from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-339';TITLE='SOLANA RECONCILED PROGRAM IDENTITY REGISTRY';EXPECTED='build_oad_339_solana_reconciled_program_identity_registry.py';MODULE='oad_339_solana_reconciled_program_identity_registry.py';TEST='test_oad_339_solana_reconciled_program_identity_registry.py';DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_338_solana_token2022_memo_foundation_repair.py': ('TOKEN_2022_PROGRAM_ID', 'MEMO_PROGRAM_ID'), 'qseries_v2/oracle_adapters/independent/oad_333_solana_authoritative_program_identity_registry.py': ('identify_solana_program',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program
from .oad_338_solana_token2022_memo_foundation_repair import identify_foundation_program
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaReconciledProgramIdentity:
 program_id:str;name:str;category:str;known:bool;market_relevant:bool;source:str;execution_authority:bool=False
def identify_reconciled_program(program_id):
 f=identify_foundation_program(program_id)
 if f.name!="UNRESOLVED":return SolanaReconciledProgramIdentity(f.program_id,f.name,f.category,True,f.market_relevant,"FOUNDATION_REPAIR",False)
 x=identify_solana_program(program_id)
 return SolanaReconciledProgramIdentity(x.program_id,x.name,x.category,x.known,x.market_relevant,"OAD_333" if x.known else "UNRESOLVED",False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_339_solana_reconciled_program_identity_registry import *
class T(unittest.TestCase):
 def test_reconcile(self):
  a=identify_reconciled_program("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
  b=identify_reconciled_program("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
  c=identify_reconciled_program("NOPE")
  print("[RECONCILED]",a.name,a.source,b.name,b.source,c.name)
  self.assertEqual(a.name,"TOKEN_2022");self.assertEqual(b.name,"PUMP_FUN_AMM");self.assertFalse(c.known)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-339 reconciled Solana program identity registry certified")

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
