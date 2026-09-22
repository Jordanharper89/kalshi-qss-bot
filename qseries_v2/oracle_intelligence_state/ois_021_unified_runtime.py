from dataclasses import dataclass

OIS_021_BUILD_ID="OIS-021"
OIS_021_REVISION="OIS_021_UNIFIED_ORACLE_RUNTIME_COMPOSITION_V1"

@dataclass(frozen=True)
class RuntimeComponent:
    name:str
    role:str
    read_only_upstream:bool

@dataclass(frozen=True)
class UnifiedOracleRuntimeGraph:
    components:tuple[RuntimeComponent,...]
    terminal_dependency:bool
    execution_authority:bool

def build_unified_oracle_runtime_graph():
    names=(
        ("live_shadow","continuous_market_observation",True),
        ("postgresql","durable_state_and_history",False),
        ("observation_intelligence","observation_processing",True),
        ("umd","market_universe_and_identity",True),
        ("oml","oracle_memory",True),
        ("ocl","continuous_learning",True),
        ("osr","scientific_reasoning",True),
        ("ois","canonical_intelligence_state",False),
    )
    return UnifiedOracleRuntimeGraph(tuple(RuntimeComponent(*x) for x in names),False,False)

def verify_ois_021_unified_oracle_runtime_composition():
    g=build_unified_oracle_runtime_graph()
    return (
        len(g.components)==8
        and not g.terminal_dependency
        and not g.execution_authority
        and {x.name for x in g.components}=={"live_shadow","postgresql","observation_intelligence","umd","oml","ocl","osr","ois"}
    )
