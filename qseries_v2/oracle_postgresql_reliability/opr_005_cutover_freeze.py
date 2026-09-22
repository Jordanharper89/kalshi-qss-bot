from __future__ import annotations
from pathlib import Path
import ast,hashlib,json

from .opr_004_persistent_ingress_wrappers import read_children,safe_name

OPR_005_BUILD_ID="OPR-005"
OPR_005_REVISION="OPR_005_PHYSICAL_CONNECTION_REUSE_CUTOVER_FREEZE_V1"
WRITER="run_opr_003_persistent_single_writer_runtime.py"

def patch_child(source,name,value):
    tree=ast.parse(source);node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets
        ):
            node=item.value;break
    if node is None:raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)==name and isinstance(v,ast.Constant):
            old=str(v.value)
            if old==value:return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(value),1)
                    out="".join(lines);ast.parse(out);return out
    raise RuntimeError(f"child {name} not found")

def verify_cutover(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    children=read_children(launcher.read_text(encoding="utf-8"))
    if children.get("canonical_writer")!=WRITER:return False
    for name,runner in children.items():
        if name=="canonical_writer":continue
        if runner!=f"run_opr_004_{safe_name(name)}_persistent_ingress.py":return False
    return True

def write_manifest(root,learning_underlying):
    root=Path(root).resolve()
    children=read_children((root/"run_oracle_LIVE.py").read_text(encoding="utf-8"))
    body={
        "build_id":OPR_005_BUILD_ID,
        "revision":OPR_005_REVISION,
        "canonical_writer":children.get("canonical_writer"),
        "producer_children":{k:v for k,v in children.items() if k!="canonical_writer"},
        "learning_underlying_preserved":learning_underlying,
        "persistent_queue_sessions":True,
        "single_writer_advisory_lease":True,
        "oph_queue_schema_preserved":True,
        "execution_authority":False,
    }
    payload=json.dumps(body,sort_keys=True,separators=(",",":"))
    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_postgresql_reliability"/"OPR_005_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body
