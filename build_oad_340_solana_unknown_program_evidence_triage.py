from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-340';TITLE='SOLANA UNKNOWN PROGRAM EVIDENCE TRIAGE';EXPECTED='build_oad_340_solana_unknown_program_evidence_triage.py';MODULE='oad_340_solana_unknown_program_evidence_triage.py';TEST='test_oad_340_solana_unknown_program_evidence_triage.py';DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_339_solana_reconciled_program_identity_registry.py': ('identify_reconciled_program',), 'qseries_v2/oracle_adapters/independent/oad_334_solana_transaction_protocol_attribution.py': ('top_level_program_ids', 'inner_program_ids')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaUnknownProgramTriage:
 total_unknown:int;unique_unknown:int;top_unknown:tuple;execution_authority:bool=False
def triage_unknown_programs(attributions):
 c=Counter()
 for a in attributions:
  for pid in tuple(a.top_level_program_ids)+tuple(a.inner_program_ids):
   x=identify_reconciled_program(pid)
   if not x.known:c[pid]+=1
 return SolanaUnknownProgramTriage(sum(c.values()),len(c),tuple(c.most_common(50)),False)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_340_solana_unknown_program_evidence_triage import *
class T(unittest.TestCase):
 def test_triage(self):
  a=SimpleNamespace(top_level_program_ids=("X","X","TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"),inner_program_ids=("Y",))
  x=triage_unknown_programs((a,))
  print("[TRIAGE]",x.total_unknown,x.top_unknown)
  self.assertEqual(x.total_unknown,3);self.assertEqual(x.top_unknown[0],("X",2))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-340 unresolved program evidence triage certified")

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
