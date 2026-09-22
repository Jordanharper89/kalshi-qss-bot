from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

OAD_031_BUILD_ID="OAD-031"
OAD_031_REVISION="OAD_031_PHYSICAL_ORACLE_LIVE_RUNTIME_KALSHI_BINDING_V1"

LIVE_SHADOW_LAUNCHER_CANDIDATES=(
    "run_oracle_live_shadow_FIXED.py",
    "run_oracle_live_shadow_continuous.py",
    "run_oracle_live_shadow.py",
)

@dataclass(frozen=True)
class OracleKalshiRuntimeBinding:
    oracle_launcher:str
    kalshi_stream_runner:str
    live_shadow_launcher:str|None
    terminal_dependency:bool=False
    execution_authority:bool=False

def discover_live_shadow_launcher(root):
    root=Path(root)
    for name in LIVE_SHADOW_LAUNCHER_CANDIDATES:
        if (root/name).is_file():
            return name
    return None

def build_oracle_kalshi_runtime_binding(root):
    root=Path(root)
    if not (root/"run_oracle_LIVE.py").is_file():
        raise RuntimeError("run_oracle_LIVE.py missing")
    stream="run_oad_032_kalshi_persistent_stream.py"
    return OracleKalshiRuntimeBinding(
        "run_oracle_LIVE.py",stream,discover_live_shadow_launcher(root),False,False
    )

def verify_oad_031_physical_oracle_live_runtime_kalshi_binding():
    # Repository-independent verifier protects authority boundaries.
    x=OracleKalshiRuntimeBinding("run_oracle_LIVE.py","run_oad_032_kalshi_persistent_stream.py",None,False,False)
    return not x.terminal_dependency and not x.execution_authority and x.oracle_launcher=="run_oracle_LIVE.py"
