from dataclasses import dataclass

@dataclass(frozen=True)
class CoverageGapClassification:
    coverage_rate:float
    severity:str
    likely_gap:str
    recommended_next_capability:str
    execution_authority:bool=False

def classify_coverage_gap(result):
    r=float(result.coverage_rate)
    if result.sampled_markets==0:
        return CoverageGapClassification(0,"UNKNOWN","NO_DENOMINATOR","verify_sampling",False)
    if r>=.9:
        return CoverageGapClassification(r,"LOW","MINOR_QUIET_MARKET_GAP","targeted_quiet_market_snapshot_coverage",False)
    if r>=.6:
        return CoverageGapClassification(r,"MODERATE","PARTIAL_PRE_SETTLEMENT_COVERAGE","expand_snapshot_and_canonical_admission_coverage",False)
    if r>=.2:
        return CoverageGapClassification(r,"HIGH","MAJOR_PRE_SETTLEMENT_COVERAGE_GAP","trace_acquisition_to_canonicalization_path",False)
    return CoverageGapClassification(r,"CRITICAL","SYSTEMIC_PRE_SETTLEMENT_COVERAGE_GAP","build_universal_pre_settlement_snapshot_path",False)

def verify_opc_004_live_coverage_gap_classifier():
    class X:
        sampled_markets=100
        coverage_rate=.1
    return classify_coverage_gap(X()).severity=="CRITICAL"
