from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake

OCR_009_BUILD_ID="OCR-009"
OCR_009_REVISION="OCR_009_INTELLIGENCE_STATE_PROJECTION_V1"

@dataclass(frozen=True)
class LiveIntelligenceProjection:
    market_ticker:str
    ois_intake:object
    source_osr_hash:str
    read_only:bool=True
    writes_frozen_ois:bool=False

def project_reasoning_result_to_ois(result):
    s=result.osr_state
    intake=build_osr_state_intake(result.market_ticker,s.reasoning_state,s.support,s.confidence,s.contradiction,s.abstain,s.state_hash)
    return LiveIntelligenceProjection(result.market_ticker,intake,s.state_hash,True,False)

def project_reasoning_results(results):
    return tuple(project_reasoning_result_to_ois(x) for x in results)

def verify_ocr_009_intelligence_state_projection():
    from .ocr_007_umd_context_join import join_rows_to_umd_context
    from .ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
    obs=join_rows_to_umd_context(({"observation_id":"1","ticker":"KXTEST"},{"observation_id":"2","ticker":"KXTEST"}))
    x=project_reasoning_results(reason_over_market_aware_observations(obs))[0]
    return x.ois_intake.read_only and x.read_only and not x.writes_frozen_ois
