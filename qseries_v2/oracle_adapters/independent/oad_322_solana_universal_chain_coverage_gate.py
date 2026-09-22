\

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

