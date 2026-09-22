from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path

EXPECTED_CORE=frozenset({
    "fast_lane","inventory","reasoning","learning",
    "coverage","canonical_writer","continuity",
})
CRYPTO_CHILD="crypto_learning"
CRYPTO_RUNNER="run_oad_207_crypto_continuous_learning_production_child.py"

@dataclass(frozen=True,slots=True)
class CryptoLearningLauncherAdmission:
    launcher_present:bool
    expected_core_present:bool
    truthful_health_present:bool
    crypto_runner_present:bool
    crypto_child_already_present:bool
    execution_boundary_preserved:bool
    admitted:bool

def read_children(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets
        ):
            out={}
            for k,v in zip(node.value.keys,node.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                    out[str(k.value)]=str(v.value)
            return out
    raise RuntimeError("Physical run_oracle_LIVE.py CHILDREN dictionary not found")

def evaluate_crypto_learning_launcher_admission(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    runner=root/CRYPTO_RUNNER
    if not launcher.is_file():
        return CryptoLearningLauncherAdmission(False,False,False,runner.is_file(),False,False,False)
    source=launcher.read_text(encoding="utf-8")
    ast.parse(source)
    children=read_children(source)
    core=EXPECTED_CORE.issubset(children)
    truthful=all(x in source for x in (
        "STARTING","HEALTHY","DEGRADED","FAILED",
        "recent_restarts_60s","restart_backoff_seconds",
    ))
    exec_ok="execution_authority=TRUE" not in source
    already=children.get(CRYPTO_CHILD)==CRYPTO_RUNNER
    admitted=bool(core and truthful and runner.is_file() and exec_ok)
    return CryptoLearningLauncherAdmission(
        True,core,truthful,runner.is_file(),already,exec_ok,admitted
    )
