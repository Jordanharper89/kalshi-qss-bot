from __future__ import annotations
from pathlib import Path
import ast,json

OLF_005_BUILD_ID="OLF-005"
OLF_005_REVISION="OLF_005_PHYSICAL_LEARNING_TO_REASONING_CUTOVER_GATE_V1"
TARGET="run_olf_004_feedback_aware_reasoning_runtime.py"

def patch_reasoning_child(source,target=TARGET):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value;break
    if node is None:raise RuntimeError("Oracle Live CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="reasoning" and isinstance(v,ast.Constant):
            old=str(v.value)
            if old==target:return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(target),1)
                    out="".join(lines);ast.parse(out);return out
    raise RuntimeError("Oracle Live reasoning child not found")

def verify_attestation_matches_learner(root=None):
    root=Path(root or Path.cwd()).resolve()
    att=root/"runtime_state"/"oracle_learning_feedback_reasoning_attestation.json"
    state=root/"runtime_state"/"oracle_learning_runtime_state.json"
    if not att.is_file() or not state.is_file():return False
    a=json.loads(att.read_text(encoding="utf-8"))
    s=json.loads(state.read_text(encoding="utf-8"))
    ocl=s.get("ocl_state") if isinstance(s,dict) else {}
    current=str((ocl or {}).get("state_hash") or "")
    return (
        bool(current)
        and str(a.get("learner_state_hash") or "")==current
        and int(a.get("markets_reasoned",0))>0
        and a.get("execution_authority") is False
    )

def verify_olf_005_physical_learning_to_reasoning_cutover_gate():
    return OLF_005_BUILD_ID=="OLF-005" and callable(patch_reasoning_child)
