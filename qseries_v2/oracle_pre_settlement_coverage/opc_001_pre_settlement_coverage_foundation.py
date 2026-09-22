from dataclasses import dataclass

@dataclass(frozen=True)
class PreSettlementCoveragePolicy:
    venue:str="KALSHI"
    bounded_sampling:bool=True
    read_only:bool=True
    olr_access:str="READ_ONLY"
    execution_authority:bool=False

def build_pre_settlement_coverage_policy():
    return PreSettlementCoveragePolicy()

def verify_opc_001_pre_settlement_coverage_foundation():
    p=build_pre_settlement_coverage_policy()
    return p.venue=="KALSHI" and p.bounded_sampling and p.read_only and p.olr_access=="READ_ONLY" and not p.execution_authority
