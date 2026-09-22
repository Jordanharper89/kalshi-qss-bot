from dataclasses import dataclass
from .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings
from .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from .oad_218_existing_ocl_state_hash_envelope import envelope
from qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import update_source_reliability
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
PROVIDERS=frozenset(("coinbase","bitcoin","ethereum","solana"))
@dataclass(frozen=True,slots=True)
class ExactReliabilityState:
 scored_cases:int;source_states:tuple;source_reliability_state_hash:str|None;rejected_non_provider_claims:int;state:str;probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False
def materialize_exact_provider_source_reliability(root=None):
 by={x.experience_id:x for x in read_crypto_learned_case_history(root=root,per_asset_limit=512)};states={};reject=0;cases=0
 for b in read_exact_prospective_bindings(root):
  x=by.get(b.experience_id)
  if x is None:continue
  y=float(x.return_fraction)>0;used=False
  for c in b.source_claims:
   if len(c)<4 or str(c[0]).lower() not in PROVIDERS:reject+=1;continue
   s=str(c[0]).lower();states[s]=update_source_reliability(states.get(s),s,bool(c[3])==y);used=True
  cases+=1 if used else 0
 ss=tuple(states[k] for k in sorted(states))
 if not ss:return ExactReliabilityState(0,(),None,reject,"HOLD_PROVIDER_OUTCOME_EVIDENCE_REQUIRED")
 return ExactReliabilityState(cases,ss,envelope("prospective_provider_source_reliability",ss).state_hash,reject,"MATERIALIZED")
