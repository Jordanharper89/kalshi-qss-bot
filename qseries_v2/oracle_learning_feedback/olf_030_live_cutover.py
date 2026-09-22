from __future__ import annotations
import ast
TARGET="run_olf_030_breadth_aware_reasoning_runtime.py"
def patch_reasoning_child(source,target=TARGET):
    tree=ast.parse(source);node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):node=item.value;break
    if node is None:raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="reasoning" and isinstance(v,ast.Constant):
            old=str(v.value)
            if old==target:return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(target),1);out="".join(lines);ast.parse(out);return out
    raise RuntimeError("reasoning child not found")
