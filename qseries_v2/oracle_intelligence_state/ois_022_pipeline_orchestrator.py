from dataclasses import dataclass
from hashlib import sha256
import json
from .ois_021_unified_runtime import UnifiedOracleRuntimeGraph

OIS_022_BUILD_ID="OIS-022"
OIS_022_REVISION="OIS_022_CONTINUOUS_PIPELINE_CYCLE_ORCHESTRATOR_V1"

@dataclass(frozen=True)
class RuntimeCycle:
    sequence:int
    stages:tuple[str,...]
    cycle_hash:str
    terminal_dependency:bool=False

def run_runtime_cycle(graph,sequence):
    if not isinstance(graph,UnifiedOracleRuntimeGraph) or sequence<1:
        raise ValueError("certified runtime graph and positive sequence required")
    stages=tuple(x.name for x in graph.components)
    raw={"sequence":sequence,"stages":stages,"terminal_dependency":False}
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return RuntimeCycle(sequence,stages,h,False)

def verify_ois_022_continuous_pipeline_cycle_orchestrator():
    from .ois_021_unified_runtime import build_unified_oracle_runtime_graph
    c=run_runtime_cycle(build_unified_oracle_runtime_graph(),1)
    return not c.terminal_dependency and c.stages[-1]=="ois" and len(c.cycle_hash)==64
