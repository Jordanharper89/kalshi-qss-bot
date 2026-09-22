from __future__ import annotations
import ast, os, subprocess, sys
from pathlib import Path

GMGN_CHILD="gmgn_intelligence"
GMGN_RUNNER="run_oad_284_gmgn_continuous_intelligence_production_child.py"

def root():
    from pathlib import Path
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def read_children_node(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):
            children={}
            for k,v in zip(node.value.keys,node.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                    children[str(k.value)]=str(v.value)
            return node,children
    raise RuntimeError("Physical CHILDREN dictionary not found")

def patch_children(source):
    node,before=read_children_node(source)
    required={"fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity","recovery","crypto_learning"}
    missing=sorted(required-set(before))
    if missing: raise RuntimeError("Refusing integration; missing certified children: "+", ".join(missing))
    if GMGN_CHILD in before and before[GMGN_CHILD]!=GMGN_RUNNER:
        raise RuntimeError("gmgn_intelligence already bound to unexpected runner")
    if before.get(GMGN_CHILD)==GMGN_RUNNER:
        return source,before,before
    lines=source.splitlines(keepends=True)
    indent=" "*(node.col_offset+4)
    insertion=f'{indent}"{GMGN_CHILD}": "{GMGN_RUNNER}",\n'
    closing_index=node.end_lineno-1
    patched="".join(lines[:closing_index])+insertion+"".join(lines[closing_index:])
    ast.parse(patched)
    _,after=read_children_node(patched)
    if set(after)!=set(before)|{GMGN_CHILD}: raise RuntimeError("unexpected CHILDREN mutation")
    for k,v in before.items():
        if after.get(k)!=v: raise RuntimeError("existing child changed: "+k)
    return patched,before,after

def main():
    r=root()
    # Windows is case-insensitive, but use the certified physical launcher spelling from prior integration builds.
    launcher=r/"run_oracle_LIVE.py"
    runner=r/GMGN_RUNNER
    if not launcher.is_file(): raise RuntimeError("physical run_oracle_LIVE.py missing")
    if not runner.is_file(): raise RuntimeError("OAD-284 runner missing")
    original=launcher.read_text(encoding="utf-8"); ast.parse(original)
    if "for key in CHILDREN" not in original or "restart_backoff_seconds" not in original:
        raise RuntimeError("truthful ORH dynamic supervision contract missing")
    if "execution_authority=TRUE" in original: raise RuntimeError("execution boundary violation")
    patched,before,after=patch_children(original)
    old=launcher.read_bytes()
    try:
        tmp=launcher.with_suffix(".py.tmp"); tmp.write_text(patched,encoding="utf-8",newline="\n"); os.replace(tmp,launcher)
        check=launcher.read_text(encoding="utf-8")
        _,verify=read_children_node(check)
        if verify!=after: raise RuntimeError("physical CHILDREN exact readback mismatch")
        subprocess.run([sys.executable,str(launcher),"--check"],cwd=r,timeout=30,check=True)
        subprocess.run([sys.executable,str(runner),"--check"],cwd=r,timeout=30,check=True)
        print("[PASS] existing Oracle children preserved:",tuple(before))
        print("[PASS] gmgn_intelligence ->",GMGN_RUNNER)
        print("[PASS] truthful ORH dynamic supervision includes GMGN")
        print("[PASS] launcher --check passed")
        print("[PASS] GMGN child --check passed")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-285 INSTALLATION COMPLETE")
    except Exception:
        launcher.write_bytes(old)
        print("[ROLLBACK] physical launcher restored")
        raise

if __name__=="__main__": main()
