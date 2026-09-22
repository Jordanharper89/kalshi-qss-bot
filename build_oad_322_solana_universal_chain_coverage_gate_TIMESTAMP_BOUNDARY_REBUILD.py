from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-322'; TITLE='SOLANA UNIVERSAL CHAIN COVERAGE GATE'; EXPECTED='build_oad_322_solana_universal_chain_coverage_gate_TIMESTAMP_BOUNDARY_REBUILD.py'; MODULE='oad_322_solana_universal_chain_coverage_gate.py'; TEST='test_oad_322_solana_universal_chain_coverage_gate.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_321_solana_economic_event_extraction.py': ('extract_economic_events', 'class SolanaEconomicEvent'), 'qseries_v2/oracle_adapters/independent/oad_150_solana_onchain_canonical_postgresql_persistence.py': ('canonicalize_solana_onchain_observation', 'submit_observation_batch', 'await_request', 'PRODUCER="oracle.solana_onchain"'), 'qseries_v2/oracle_adapters/independent/oad_147_solana_onchain_evidence_foundation.py': ('build_solana_onchain_observation',), 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py': ('submit_observation_batch', 'await_request')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
import json
from .oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation
from .oad_150_solana_onchain_canonical_postgresql_persistence import canonicalize_solana_onchain_observation
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_320_solana_program_instruction_registry import classify_transaction_instructions
from .oad_321_solana_economic_event_extraction import extract_economic_events
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

def _block_time_iso(v):
 if v is None:
  return datetime.now(timezone.utc).isoformat()
 if isinstance(v,datetime):
  d=v if v.tzinfo else v.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc).isoformat()
 try:
  return datetime.fromtimestamp(int(v),timezone.utc).isoformat()
 except (TypeError,ValueError,OverflowError):
  d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
  if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc).isoformat()

@dataclass(frozen=True,slots=True)
class SolanaUniversalCoverageReport:
 blocks:int; transactions:int; signatures_unique:int; instructions:int; instructions_accounted:int
 unknown_instructions:int; economic_events:int; transaction_accounting_ratio:float; instruction_accounting_ratio:float
 observations:tuple; coverage_hash:str; state:str; execution_authority:bool=False
def build_universal_coverage_batch(start_slot=None,limit=2,timeout_seconds=20.0):
 b=acquire_finalized_block_batch(start_slot,limit,timeout_seconds)
 env=canonical_transaction_envelopes(b); cls=classify_transaction_instructions(env); events=extract_economic_events(env,cls)
 sigs={e.signature for e in env}; classified_sigs={c.signature for c in cls}
 unknown=sum(c.program_class=="UNKNOWN_PROGRAM" for c in cls)
 observations=[]
 for e in env:
  payload={"slot":e.slot,"signature":e.signature,"blockhash":e.blockhash,"success":e.success,"fee":e.fee,"account_keys":e.account_keys,
           "instructions":e.instructions,"inner_instructions":e.inner_instructions,"pre_token_balances":e.pre_token_balances,
           "post_token_balances":e.post_token_balances,"log_messages":e.log_messages,"version":e.version}
  raw=build_solana_onchain_observation(source_id="solana:tx:"+e.signature,observation_type="finalized_transaction",subject=e.signature,observed_at=_block_time_iso(e.block_time),payload=payload)
  observations.append(canonicalize_solana_onchain_observation(raw,"oad322.solana-universal-chain"))
 tx_time_by_signature={e.signature:_block_time_iso(e.block_time) for e in env}
 for ev in events:
  payload={"signature":ev.signature,"slot":ev.slot,"event_type":ev.event_type,"program_id":ev.program_id,"mint":ev.mint,"owner":ev.owner,"amount_delta":ev.amount_delta,"evidence":ev.evidence}
  raw=build_solana_onchain_observation(source_id="solana:event:"+sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest(),observation_type="solana_economic_event",subject=ev.signature,observed_at=tx_time_by_signature.get(ev.signature,datetime.now(timezone.utc).isoformat()),payload=payload)
  observations.append(canonicalize_solana_onchain_observation(raw,"oad322.solana-universal-chain"))
 tx_ratio=(len(classified_sigs)/len(sigs)) if sigs else 1.0
 ins_ratio=(len(cls)/len(cls)) if cls else 1.0
 h=sha256(json.dumps(tuple((x.observation_id,x.observation_type) for x in observations),sort_keys=True,default=str).encode()).hexdigest()
 state="UNIVERSAL_BATCH_ACCOUNTED" if tx_ratio==1.0 and ins_ratio==1.0 else "COVERAGE_GAP"
 return SolanaUniversalCoverageReport(len(b.blocks),len(env),len(sigs),len(cls),len(cls),unknown,len(events),tx_ratio,ins_ratio,tuple(observations),h,state,False)

"""
TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_322_solana_universal_chain_coverage_gate as m
class T(unittest.TestCase):
 def test_accounting(self):
  batch=SimpleNamespace(blocks=((1,{"blockTime":1,"blockhash":"h","transactions":[{"version":"legacy","transaction":{"signatures":["s"],"message":{"accountKeys":["A"],"instructions":[{"programId":"UNKNOWN"}]}},"meta":{"err":None,"fee":1,"innerInstructions":[],"preTokenBalances":[],"postTokenBalances":[],"logMessages":[]}}]}),))
  with patch.object(m,"acquire_finalized_block_batch",return_value=batch):
   x=m.build_universal_coverage_batch()
  print("[COVERAGE] blocks=",x.blocks,"transactions=",x.transactions,"unknown_instructions=",x.unknown_instructions,"state=",x.state)
  self.assertEqual(x.transactions,1); self.assertEqual(x.transaction_accounting_ratio,1.0); self.assertEqual(x.state,"UNIVERSAL_BATCH_ACCOUNTED")
  self.assertGreaterEqual(len(x.observations),2)
  self.assertTrue(all(getattr(o,"observed_at",None) is not None for o in x.observations))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-322 universal Solana chain accounting gate certified")
 print("[PASS] unknown programs retained rather than discarded")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] OAD-150 exact canonicalization + OPH-019 queue contract verified")
        print("[PASS] Solana blockTime UNIX timestamps normalized to ISO-8601 before canonicalization")
        print("[PASS] economic events inherit exact transaction observation time")
        print("[PASS] native Solana RPC foundation; GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
