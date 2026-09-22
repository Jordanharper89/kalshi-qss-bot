from __future__ import annotations
from pathlib import Path
import ast

OPR_004_BUILD_ID="OPR-004"
OPR_004_REVISION="OPR_004_PERSISTENT_INGRESS_WRAPPER_GENERATION_V1"

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets
        ):
            return {
                str(k.value):str(v.value)
                for k,v in zip(item.value.keys,item.value.values)
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)
            }
    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

def unwrap_runner(root,runner):
    current=str(runner);seen=set()
    for _ in range(20):
        if current in seen:raise RuntimeError("recursive wrapper chain")
        seen.add(current);p=Path(root)/current
        if not p.is_file():return current
        target=None
        try:
            tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
            for item in tree.body:
                if isinstance(item,ast.Assign):
                    for t in item.targets:
                        if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":
                            target=ast.literal_eval(item.value);break
                if target is not None:break
        except Exception:target=None
        if not target:return current
        current=str(target)
    raise RuntimeError("wrapper resolution exceeded")

def safe_name(name):
    return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_").lower()

def wrapper_source(child_name,underlying):
    producer="oracle."+str(child_name)
    lines=[
        "from pathlib import Path",
        "import runpy",
        "from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import install_persistent_postgresql_ingress",
        f"UNDERLYING_RUNNER={underlying!r}",
        "",
        "if __name__=='__main__':",
        "    print('='*88,flush=True)",
        f"    print(' OPR-004 PERSISTENT POSTGRESQL INGRESS child={child_name}',flush=True)",
        "    print('='*88,flush=True)",
        f"    install_persistent_postgresql_ingress({producer!r},Path.cwd())",
        "    print('[OPR-004] persistent_queue_session=TRUE direct_canonical_postgresql_write_authority=FALSE',flush=True)",
        "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')",
        "",
    ]
    source="\n".join(lines);ast.parse(source);return source

def verify_opr_004_persistent_ingress_wrapper_generation(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    if not launcher.is_file():return False
    children=read_children(launcher.read_text(encoding="utf-8"))
    return bool(children) and "canonical_writer" in children
