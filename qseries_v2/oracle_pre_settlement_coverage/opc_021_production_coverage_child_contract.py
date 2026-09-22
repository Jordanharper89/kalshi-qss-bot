from dataclasses import dataclass
@dataclass(frozen=True)
class ProductionCoverageChildContract:
    child_name:str="coverage"
    runner_name:str="run_opc_025_continuous_coverage_child.py"
    terminal_dependency:bool=False
    execution_authority:bool=False
    restart_supervised:bool=True
    durable_resume:bool=True
    full_universe_rotation:bool=True
def build_production_coverage_child_contract(): return ProductionCoverageChildContract()
def verify_opc_021_production_coverage_child_contract():
    c=build_production_coverage_child_contract()
    return c.child_name=="coverage" and c.restart_supervised and c.durable_resume and c.full_universe_rotation and not c.terminal_dependency and not c.execution_authority
