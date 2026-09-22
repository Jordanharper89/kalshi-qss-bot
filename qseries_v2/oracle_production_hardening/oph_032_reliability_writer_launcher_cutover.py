from __future__ import annotations
from pathlib import Path
import ast

OPH_032_BUILD_ID="OPH-032"
OPH_032_REVISION="OPH_032_RELIABILITY_WRITER_LAUNCHER_CUTOVER_V1"
RELIABILITY_WRITER="run_oph_031_classified_single_writer_reliability_runtime.py"

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets
        ):
            result={}
            for k,v in zip(item.value.keys,item.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                    result[str(k.value)]=str(v.value)
            return result
    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

def patch_canonical_writer(source):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets
        ):
            node=item.value
            break
    if node is None: raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="canonical_writer" and isinstance(v,ast.Constant):
            old=str(v.value)
            if old==RELIABILITY_WRITER:return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(RELIABILITY_WRITER),1)
                    patched="".join(lines);ast.parse(patched);return patched
    raise RuntimeError("canonical_writer child not found")

def verify_oph_032_reliability_writer_launcher_cutover(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    if not launcher.is_file(): return False
    children=read_children(launcher.read_text(encoding="utf-8"))
    if children.get("canonical_writer")!=RELIABILITY_WRITER:return False
    producer_names=[n for n in children if n!="canonical_writer"]
    if not producer_names:return False
    for name in producer_names:
        runner=children[name]
        if not runner.startswith("run_oph_022_") or not runner.endswith("_postgresql_ingress.py"):
            return False
    return True
