from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-342';TITLE='SOLANA FOUNDATION REPAIR PHYSICAL COVERAGE GATE';EXPECTED='build_oad_342_solana_foundation_repair_physical_coverage_gate.py';MODULE='oad_342_solana_foundation_repair_physical_coverage_gate.py';TEST='test_oad_342_solana_foundation_repair_physical_coverage_gate.py';DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_338_solana_token2022_memo_foundation_repair.py': ('TOKEN_2022_PROGRAM_ID', 'MEMO_PROGRAM_ID'), 'qseries_v2/oracle_adapters/independent/oad_340_solana_unknown_program_evidence_triage.py': ('triage_unknown_programs',), 'qseries_v2/oracle_adapters/independent/oad_341_solana_token2022_activity_decoder.py': ('decode_token2022_activity',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program
from .oad_340_solana_unknown_program_evidence_triage import triage_unknown_programs
from .oad_341_solana_token2022_activity_decoder import decode_token2022_activity
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
BASELINE_AUTHORITATIVE_RATIO=0.8424611223799865
BASELINE_ECONOMIC_RATIO=0.7020460358056266
@dataclass(frozen=True,slots=True)
class SolanaFoundationRepairPhysicalReport:
 blocks:int;transactions:int;program_invocations:int;known:int;infrastructure:int;economic_known:int;unknown:int
 known_ratio:float;economic_resolution_ratio:float;token2022_invocations:int;token2022_transactions:int;wallet_flows:int
 top_unknown_programs:tuple;state:str;execution_authority:bool=False
def measure_foundation_repair_physical(block_limit=1,timeout_seconds=25.0):
 b=acquire_finalized_block_batch(None,block_limit,timeout_seconds);env=canonical_transaction_envelopes(b);attr=attribute_transaction_protocols(env);flows=build_wallet_token_flows(env)
 ids=[]
 for a in attr:ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))
 known=infra=econ=t22=0
 for pid in ids:
  x=identify_reconciled_program(pid)
  if x.known:
   known+=1
   if x.category=="INFRASTRUCTURE":infra+=1
   else:econ+=1
  if x.name=="TOKEN_2022":t22+=1
 unknown=len(ids)-known;ratio=known/len(ids) if ids else 1.0;den=econ+unknown;er=econ/den if den else 1.0
 tri=triage_unknown_programs(attr);acts=decode_token2022_activity(env,attr,flows)
 return SolanaFoundationRepairPhysicalReport(len(b.blocks),len(env),len(ids),known,infra,econ,unknown,ratio,er,t22,len(acts),len(flows),tri.top_unknown,"FOUNDATION_REPAIR_COVERAGE_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_342_solana_foundation_repair_physical_coverage_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  x=measure_foundation_repair_physical(1)
  print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
  print("[PHYSICAL] known_ratio=",x.known_ratio,"economic_resolution_ratio=",x.economic_resolution_ratio)
  print("[PHYSICAL] known=",x.known,"infrastructure=",x.infrastructure,"economic_known=",x.economic_known,"unknown=",x.unknown)
  print("[PHYSICAL] token2022_invocations=",x.token2022_invocations,"token2022_transactions=",x.token2022_transactions,"wallet_flows=",x.wallet_flows)
  print("[PHYSICAL] top_unknown_programs=",x.top_unknown_programs[:12])
  self.assertGreater(x.transactions,0);self.assertGreater(x.program_invocations,0);self.assertEqual(x.state,"FOUNDATION_REPAIR_COVERAGE_MEASURED")
  self.assertGreater(x.token2022_invocations,0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-342 physical Solana Token-2022/Memo foundation repair measured")
 print("[PASS] unresolved program identities retained for evidence-driven attribution")

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
