from dataclasses import dataclass

OIS_051_BUILD_ID="OIS-051"
OIS_051_REVISION="OIS_051_ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_CONTRACT_V1"

@dataclass(frozen=True)
class OracleRuntimeLaunchContract:
    launcher_name:str
    runtime_name:str
    terminal_dependency:bool
    requires_certified_dependencies:bool
    execution_authority:bool
    continuous:bool

def build_oracle_runtime_launch_contract(launcher_name="run_oracle_LIVE.py"):
    if not launcher_name:
        raise ValueError("launcher_name required")
    return OracleRuntimeLaunchContract(
        launcher_name,
        "Oracle Live Runtime",
        False,
        True,
        False,
        True,
    )

def verify_ois_051_oracle_live_runtime_production_launcher_contract():
    x=build_oracle_runtime_launch_contract()
    return (
        x.launcher_name=="run_oracle_LIVE.py"
        and x.runtime_name=="Oracle Live Runtime"
        and not x.terminal_dependency
        and x.requires_certified_dependencies
        and not x.execution_authority
        and x.continuous
    )
