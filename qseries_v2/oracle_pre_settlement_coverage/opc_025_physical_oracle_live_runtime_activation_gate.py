import importlib
from dataclasses import dataclass
@dataclass(frozen=True)
class OPC025Activation:
    child_name:str;runner_name:str;certified:bool;terminal_dependency:bool=False;execution_authority:bool=False
def verify_opc_025_physical_oracle_live_runtime_activation_gate():
    checks=(("opc_021_production_coverage_child_contract","verify_opc_021_production_coverage_child_contract"),("opc_022_rotating_universe_cursor_load_budget","verify_opc_022_rotating_universe_cursor_load_budget"),("opc_023_rotating_full_universe_coverage_cycle","verify_opc_023_rotating_full_universe_coverage_cycle"),("opc_024_supervised_24x7_coverage_runtime","verify_opc_024_supervised_24x7_coverage_runtime"))
    return all(getattr(importlib.import_module("qseries_v2.oracle_pre_settlement_coverage."+m),f)() for m,f in checks)
def activation_report():
    if not verify_opc_025_physical_oracle_live_runtime_activation_gate(): raise RuntimeError("OPC activation failed")
    return OPC025Activation("coverage","run_opc_025_continuous_coverage_child.py",True,False,False)
