from __future__ import annotations
import importlib
from dataclasses import dataclass

OPC_035_BUILD_ID="OPC-035"
OPC_035_REVISION="OPC_035_PRIORITY_PERSISTENCE_ACTIVATION_GATE_V1"

@dataclass(frozen=True)
class PriorityPersistenceActivation:
    fast_lane_wrapped:bool
    coverage_wrapped:bool
    frozen_oad_modified:bool=False
    frozen_ola_modified:bool=False
    execution_authority:bool=False

def verify_opc_035_priority_persistence_activation_gate():
    checks=(
        ("opc_031_persistence_priority_contract","verify_opc_031_persistence_priority_contract"),
        ("opc_032_cross_process_persistence_arbiter","verify_opc_032_cross_process_persistence_arbiter"),
        ("opc_033_priority_router_patch","verify_opc_033_priority_router_patch"),
        ("opc_034_coverage_microbatch_yield_policy","verify_opc_034_coverage_microbatch_yield_policy"),
    )
    return all(
        getattr(
            importlib.import_module(
                "qseries_v2.oracle_pre_settlement_coverage."+mod
            ),
            fn,
        )()
        for mod,fn in checks
    )

def activation_report():
    if not verify_opc_035_priority_persistence_activation_gate():
        raise RuntimeError("OPC-031 through OPC-035 verification failed")
    return PriorityPersistenceActivation(True,True,False,False,False)
