from pathlib import Path
import ast

R=Path.cwd()
roots=[R/"qseries_v2"/"oracle_predictive_data",R/"qseries_v2"/"oracle_predictive_discovery"]

def one(prefix):
    hits=[]
    for d in roots:
        if d.is_dir():
            hits += [x for x in d.glob(prefix+"*.py") if not x.name.startswith(("build_","test_"))]
    if len(hits)!=1:
        raise RuntimeError(f"{prefix}: expected exactly 1 source, found {len(hits)}: {hits}")
    return hits[0]

def dump(path):
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text)
    print("="*100)
    print("[FILE]",path.relative_to(R))
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            args=[]
            pos=n.args.posonlyargs+n.args.args
            defaults=[None]*(len(pos)-len(n.args.defaults))+list(n.args.defaults)
            for a,d in zip(pos,defaults):
                args.append(a.arg if d is None else f"{a.arg}={ast.unparse(d)}")
            if n.args.vararg: args.append("*"+n.args.vararg.arg)
            args += [f"{a.arg}={ast.unparse(d) if d else '<required>'}" for a,d in zip(n.args.kwonlyargs,n.args.kw_defaults)]
            if n.args.kwarg: args.append("**"+n.args.kwarg.arg)
            print(f"[FUNCTION] {n.name}({', '.join(args)})")
    print("="*100)

dump(one("opd_032_"))
dump(one("opd_036_"))
print("[PASS] exact OPD-032/036 interfaces inspected read-only; no production files changed")