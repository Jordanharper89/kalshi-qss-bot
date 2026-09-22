from __future__ import annotations
from pathlib import Path
import ast

OLR_046_BUILD_ID="OLR-046"
OLR_046_REVISION="OLR_046_ORACLE_LIVE_EVIDENCE_LEARNER_LAUNCHER_CUTOVER_V1"
TARGET_LEARNING_RUNNER="run_olr_044_continuous_learning_with_evidence.py"

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                out={}
                for k,v in zip(item.value.keys,item.value.values):
                    if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                        out[str(k.value)]=str(v.value)
                return out
    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

def patch_learning_child(source,target=TARGET_LEARNING_RUNNER):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value;break
    if node is None: raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="learning" and isinstance(v,ast.Constant):
            old=str(v.value)
            if old==target:return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(target),1)
                    patched="".join(lines);ast.parse(patched);return patched
    raise RuntimeError("learning child not found")

def verify_olr_046_oracle_live_evidence_learner_launcher_cutover(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    if not launcher.is_file():return False
    children=read_children(launcher.read_text(encoding="utf-8"))
    return (
        children.get("learning")==TARGET_LEARNING_RUNNER
        and (root/TARGET_LEARNING_RUNNER).is_file()
    )
