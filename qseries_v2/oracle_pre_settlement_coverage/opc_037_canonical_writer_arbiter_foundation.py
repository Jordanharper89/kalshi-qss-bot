from __future__ import annotations
from dataclasses import dataclass

OPC_037_BUILD_ID="OPC-037"
OPC_037_REVISION="OPC_037_CANONICAL_WRITER_ARBITER_FOUNDATION_V1"

@dataclass(frozen=True)
class CanonicalWriterPolicy:
    writer:str
    priority:int
    retry_limit:int
    retry_base_seconds:float
    lease_timeout_seconds:float
    execution_authority:bool=False

FAST_LANE_POLICY=CanonicalWriterPolicy(
    "FAST_LANE",100,8,0.005,5.0,False
)

COVERAGE_POLICY=CanonicalWriterPolicy(
    "COVERAGE",20,8,0.025,10.0,False
)

def writer_policy(writer):
    name=str(writer).strip().upper()
    if name=="FAST_LANE":
        return FAST_LANE_POLICY
    if name=="COVERAGE":
        return COVERAGE_POLICY
    raise ValueError("unsupported canonical writer")

def verify_opc_037_canonical_writer_arbiter_foundation():
    return (
        FAST_LANE_POLICY.priority>COVERAGE_POLICY.priority
        and FAST_LANE_POLICY.retry_base_seconds<COVERAGE_POLICY.retry_base_seconds
        and FAST_LANE_POLICY.retry_limit>=5
        and COVERAGE_POLICY.retry_limit>=5
        and not FAST_LANE_POLICY.execution_authority
        and not COVERAGE_POLICY.execution_authority
    )
