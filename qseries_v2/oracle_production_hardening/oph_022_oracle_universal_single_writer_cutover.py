from __future__ import annotations
from pathlib import Path
import ast

OPH_022_BUILD_ID="OPH-022"
OPH_022_REVISION="OPH_022_ORACLE_UNIVERSAL_SINGLE_WRITER_CUTOVER_CORRECTION_V2"
CANONICAL_WRITER="run_oph_021_exclusive_postgresql_canonical_writer.py"

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if (
            isinstance(item,ast.Assign)
            and isinstance(item.value,ast.Dict)
            and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets)
        ):
            result={}
            for k,v in zip(item.value.keys,item.value.values):
                if (
                    isinstance(k,ast.Constant)
                    and isinstance(v,ast.Constant)
                    and isinstance(v.value,str)
                ):
                    result[str(k.value)]=str(v.value)
            return result
    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

def patch_child(source,name,value):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if (
            isinstance(item,ast.Assign)
            and isinstance(item.value,ast.Dict)
            and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets)
        ):
            node=item.value
            break
    if node is None:
        raise RuntimeError("CHILDREN dictionary not found")

    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if (
            isinstance(k,ast.Constant)
            and str(k.value)==name
            and isinstance(v,ast.Constant)
            and isinstance(v.value,str)
        ):
            old=v.value
            if old==value:
                return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(value),1)
                    patched="".join(lines)
                    ast.parse(patched)
                    return patched
    raise RuntimeError(f"child {name} not found")

def unwrap_runner(root,runner):
    current=str(runner)
    seen=set()

    for _ in range(20):
        if current in seen:
            raise RuntimeError("recursive wrapper chain detected")
        seen.add(current)

        p=Path(root)/current
        if not p.is_file():
            return current

        target=None
        try:
            tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
            for item in tree.body:
                if isinstance(item,ast.Assign):
                    for t in item.targets:
                        if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":
                            target=ast.literal_eval(item.value)
                            break
                if target is not None:
                    break
        except Exception:
            target=None

        if not target:
            return current
        current=str(target)

    raise RuntimeError("wrapper resolution exceeded safety depth")

def safe_child_name(name):
    return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_").lower()

def wrapper_source(child_name,underlying):
    producer="oracle."+str(child_name)

    lines=[
        "from pathlib import Path",
        "import runpy",
        "from qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import install_universal_postgresql_ingress",
        f"UNDERLYING_RUNNER={underlying!r}",
        "",
        "if __name__=='__main__':",
        "    print('='*88,flush=True)",
        f"    print(' OPH-022 UNIVERSAL POSTGRESQL INGRESS child={child_name}',flush=True)",
        "    print('='*88,flush=True)",
        f"    install_universal_postgresql_ingress({producer!r},Path.cwd())",
        "    print('[OPH-022] direct_canonical_postgresql_write_authority=FALSE',flush=True)",
        "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')",
        "",
    ]
    source="\n".join(lines)
    ast.parse(source)
    return source

def verify_wrapper_file(path):
    path=Path(path)
    if not path.is_file():
        return False
    source=path.read_text(encoding="utf-8")
    ast.parse(source)
    if "\\n" in source.splitlines()[0]:
        return False
    return (
        "install_universal_postgresql_ingress" in source
        and "direct_canonical_postgresql_write_authority=FALSE" in source
    )

def verify_oph_022_oracle_universal_single_writer_cutover(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"

    if not launcher.is_file():
        return False

    children=read_children(launcher.read_text(encoding="utf-8"))

    if children.get("canonical_writer")!=CANONICAL_WRITER:
        return False

    producer_count=0
    for name,runner in children.items():
        if name=="canonical_writer":
            continue
        producer_count+=1
        if not runner.startswith("run_oph_022_"):
            return False
        if not runner.endswith("_postgresql_ingress.py"):
            return False
        if not verify_wrapper_file(root/runner):
            return False

    return producer_count>0
