from pathlib import Path
import ast

R=Path.cwd()

def find(prefix):
    hits=[]
    for d in (R/"qseries_v2"/"oracle_predictive_data",
              R/"qseries_v2"/"oracle_predictive_discovery"):
        if d.is_dir():
            hits += [p for p in d.glob(prefix+"*.py")
                     if not p.name.startswith(("build_","test_"))]
    if len(hits)!=1:
        raise RuntimeError(f"{prefix}: expected 1 source, found {hits}")
    return hits[0]

def dump(path):
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text)
    print("="*100)
    print("[FILE]",path.relative_to(R))
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            print("[FUNCTION]",ast.unparse(n).splitlines()[0])
    print("="*100)

dump(find("opd_033_"))
dump(find("opd_039_"))

launcher=R/"run_oracle_LIVE.py"
tree=ast.parse(launcher.read_text(encoding="utf-8"))
print("[LAUNCHER]",launcher.name)
for n in tree.body:
    if isinstance(n,ast.Assign):
        for target in n.targets:
            if isinstance(target,ast.Name) and target.id=="CHILDREN":
                children=ast.literal_eval(n.value)
                print("[CHILDREN]")
                for k,v in children.items():
                    print(f"  {k} => {v}")
print("[PASS] OPD-033/039 + unified launcher inspected read-only")