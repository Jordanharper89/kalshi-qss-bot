from __future__ import annotations
import ast, os, subprocess, sys
from pathlib import Path

REVISION="OAD_209_CRYPTO_LEARNING_ORACLE_LIVE_CHILD_INTEGRATION_V1"
CRYPTO_CHILD="crypto_learning"
CRYPTO_RUNNER="run_oad_207_crypto_continuous_learning_production_child.py"
EXPECTED_CORE={"fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity"}

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def read_children_node(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets
        ):
            children={}
            for k,v in zip(node.value.keys,node.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                    children[str(k.value)]=str(v.value)
            return node,children
    raise RuntimeError("Physical CHILDREN dictionary not found")

def patch_children(source):
    node,before=read_children_node(source)
    missing=sorted(EXPECTED_CORE-set(before))
    if missing: raise RuntimeError("Refusing launcher integration; missing core children: "+", ".join(missing))
    if CRYPTO_CHILD in before and before[CRYPTO_CHILD]!=CRYPTO_RUNNER:
        raise RuntimeError("Refusing launcher integration; crypto_learning name already bound to different runner")
    if before.get(CRYPTO_CHILD)==CRYPTO_RUNNER:
        return source,before,before
    lines=source.splitlines(keepends=True)
    indent=" "*(node.col_offset+4)
    closing_indent=" "*node.col_offset
    insertion=f'{indent}"{CRYPTO_CHILD}": "{CRYPTO_RUNNER}",\n'
    end_line=node.end_lineno
    # Insert immediately before dictionary closing line.
    closing_index=end_line-1
    patched="".join(lines[:closing_index])+insertion+"".join(lines[closing_index:])
    ast.parse(patched)
    _,after=read_children_node(patched)
    if set(after)!=set(before)|{CRYPTO_CHILD}: raise RuntimeError("Unexpected CHILDREN registry mutation")
    for k,v in before.items():
        if after.get(k)!=v: raise RuntimeError("Existing child binding changed: "+k)
    if after.get(CRYPTO_CHILD)!=CRYPTO_RUNNER: raise RuntimeError("Crypto child not installed")
    return patched,before,after

def main():
    r=root(); launcher=r/"run_oracle_LIVE.py"; runner=r/CRYPTO_RUNNER
    print("="*118)
    print(" OAD-209 CRYPTO LEARNING ORACLE LIVE CHILD INTEGRATION")
    print("="*118)
    print("[ROOT]",r)
    if not launcher.is_file(): raise RuntimeError("Physical run_oracle_LIVE.py missing")
    if not runner.is_file(): raise RuntimeError("OAD-207 production child runner missing")
    original=launcher.read_text(encoding="utf-8")
    ast.parse(original)
    if "execution_authority=TRUE" in original: raise RuntimeError("Execution boundary violation in physical launcher")
    patched,before,after=patch_children(original)
    old=launcher.read_bytes()
    try:
        tmp=launcher.with_suffix(".py.tmp"); tmp.write_text(patched,encoding="utf-8",newline="\n"); os.replace(tmp,launcher)
        physical=launcher.read_text(encoding="utf-8")
        _,verify=read_children_node(physical)
        if verify!=after: raise RuntimeError("Physical CHILDREN exact readback mismatch")
        subprocess.run([sys.executable,str(launcher),"--check"],cwd=r,timeout=30,check=True)
        subprocess.run([sys.executable,str(runner),"--check"],cwd=r,timeout=30,check=True)
        print("[PASS] existing children preserved:",tuple(before))
        print("[PASS] crypto_learning ->",CRYPTO_RUNNER)
        print("[PASS] ORH dynamic child supervision now includes crypto_learning")
        print("[PASS] physical launcher --check passed")
        print("[PASS] crypto child --check passed")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-209 INSTALLATION COMPLETE")
    except Exception:
        launcher.write_bytes(old)
        print("[ROLLBACK] physical launcher restored")
        raise
if __name__=="__main__":main()
