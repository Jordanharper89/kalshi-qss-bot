\

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

