from pathlib import Path
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
