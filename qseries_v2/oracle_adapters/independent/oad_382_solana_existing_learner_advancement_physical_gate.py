from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_378_solana_oad317_exact_case_execution import invoke_oad317_exact
from .oad_380_existing_learner_state_probe import snapshot_existing_learner_state
from .oad_381_solana_verified_runtime_case_discovery import discover_verified_runtime_cases
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class SolanaPhysicalLearningReport:
    verified_runtime_cases:int; handed_off_cases:int; handoff_result_type:str; handoff_state:str
    learner_before:tuple; learner_after:tuple; learner_advanced:bool; state:str; execution_authority:bool=False
def _dict(x): return dict(x.counters)
def measure_physical_learning_handoff(max_cases=8):
    cases=discover_verified_runtime_cases(max_cases=max_cases)
    if not cases.verified_cases:
        return SolanaPhysicalLearningReport(0,0,"NONE","NO_VERIFIED_RUNTIME_CASES",(),(),False,"NO_VERIFIED_RUNTIME_CASES",False)
    before=snapshot_existing_learner_state()
    meta,_=invoke_oad317_exact(cases.verified_cases)
    time.sleep(0.25)
    after=snapshot_existing_learner_state()
    b=_dict(before); a=_dict(after)
    advanced=any(float(a.get(k,0))>float(b.get(k,0)) for k in set(a)|set(b))
    state="PHYSICAL_EXISTING_LEARNER_ADVANCED" if advanced else "HANDOFF_EXECUTED_LEARNER_ADVANCE_NOT_OBSERVED"
    return SolanaPhysicalLearningReport(len(cases.verified_cases),meta.cases_count,meta.result_type,meta.result_state,before.counters,after.counters,advanced,state,False)
