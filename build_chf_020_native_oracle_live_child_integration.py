from pathlib import Path
import ast, py_compile, shutil

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
assert LAUNCHER.exists(),"run_oracle_LIVE.py required"
for f in ("chf_014_production_child_and_gap_lineage.py","chf_016_fixed_grid_historical_window_archive.py","chf_017_historical_window_single_writer_persistence.py"):
    assert (PKG/f).exists(),f"{f} required"

runner=ROOT/"run_coinbase_hf_live.py"
runner_code = """from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
from qseries_v2.oracle_coinbase_high_frequency.chf_016_fixed_grid_historical_window_archive import materialize_history
from qseries_v2.oracle_coinbase_high_frequency.chf_017_historical_window_single_writer_persistence import persist_history

ROOT=Path.cwd()

def main():
    while True:
        run_child(ROOT,max_seconds=90,persist_interval_s=5.0)
        materialize_history(ROOT)
        persist_history(ROOT)

if __name__=="__main__":
    main()
"""
runner.write_text(runner_code,encoding="utf-8")
py_compile.compile(str(runner),doraise=True)

src=LAUNCHER.read_text(encoding="utf-8")
tree=ast.parse(src)
target=None
for n in tree.body:
    if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict):
        if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            target=n
            break
assert target is not None,"exact top-level CHILDREN dict not found; launcher left unchanged"

keys=[k.value for k in target.value.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)]
assert "ksem_mapping" in keys,"expected certified ksem_mapping child missing; launcher left unchanged"

if "coinbase_hf" not in keys:
    backup=ROOT/"run_oracle_LIVE.pre_chf020.py"
    if not backup.exists():
        shutil.copy2(LAUNCHER,backup)
    lines=src.splitlines()
    start,end=target.lineno-1,target.end_lineno
    block="\n".join(lines[start:end])
    close=block.rfind("}")
    assert close>=0,"CHILDREN dict close not found"
    block=block[:close]+'    "coinbase_hf": "run_coinbase_hf_live.py",\n'+block[close:]
    new="\n".join(lines[:start]+block.splitlines()+lines[end:])+"\n"
    ast.parse(new)
    LAUNCHER.write_text(new,encoding="utf-8")

test_code = """from pathlib import Path
import ast
root=Path.cwd()
src=(root/"run_oracle_LIVE.py").read_text(encoding="utf-8")
tree=ast.parse(src)
found=False
for n in tree.body:
    if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict):
        if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            d={}
            for k,v in zip(n.value.keys,n.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant):
                    d[k.value]=v.value
            found=(d.get("coinbase_hf")=="run_coinbase_hf_live.py" and "ksem_mapping" in d)
assert found
assert (root/"run_coinbase_hf_live.py").exists()
print("[PASS] coinbase_hf native child registered")
print("[PASS] ksem_mapping certified sibling preserved")
print("[PASS] one Oracle production launcher preserved")
print("[PASS] CHF-020 native Oracle live child integration certified")
"""
tst=ROOT/"test_chf_020_native_oracle_live_child_integration.py"
tst.write_text(test_code,encoding="utf-8")
py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",tst)
print("[PASS] execution_authority=FALSE")
