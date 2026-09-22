
from __future__ import annotations
import importlib
from dataclasses import dataclass

@dataclass(frozen=True)
class CoverageRuntimeIntegrationReport:
    certified_start:str
    certified_end:str
    physical_cycle_ready:bool
    durable_state_ready:bool
    bounded_runtime_ready:bool
    recovery_supervision_ready:bool
    oracle_live_child_ready:bool
    terminal_dependency:bool=False
    execution_authority:bool=False

def verify_opc_020_oracle_live_runtime_integration_gate():
    checks=(
        ("opc_016_physical_coverage_cycle_adapter","verify_opc_016_physical_coverage_cycle_adapter"),
        ("opc_017_durable_coverage_runtime_state","verify_opc_017_durable_coverage_runtime_state"),
        ("opc_018_bounded_continuous_coverage_runner","verify_opc_018_bounded_continuous_coverage_runner"),
        ("opc_019_coverage_recovery_health_supervision","verify_opc_019_coverage_recovery_health_supervision"),
    )
    for mod,fn in checks:
        m=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage."+mod)
        if getattr(m,fn)() is not True:
            return False
    return True

def integration_report():
    if not verify_opc_020_oracle_live_runtime_integration_gate():
        raise RuntimeError("OPC-016 through OPC-020 verification failed")
    return CoverageRuntimeIntegrationReport(
        "OPC-016","OPC-020",True,True,True,True,True,False,False
    )
