from pathlib import Path
import ast

ROOT=Path.cwd()
BASE=ROOT/"qseries_v2/oracle_intelligence/opportunity_operating_system"
OUT=ROOT/"OOI_003_EXISTING_OOS_SEMANTIC_CONTRACT.txt"

def args(n):
    a=n.args
    names=[x.arg for x in a.posonlyargs+a.args]
    if a.vararg: names.append("*"+a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg: names.append("**"+a.kwarg.arg)
    return names

lines=[]
for p in sorted(BASE.glob("*.py")):
    tree=ast.parse(p.read_text(encoding="utf-8"))
    lines.append(f"[MODULE] {p.name}")
    for n in tree.body:
        if isinstance(n,ast.ClassDef):
            lines.append(f"  [CLASS] {n.name}")
            fields=[]
            for x in n.body:
                if isinstance(x,ast.AnnAssign) and isinstance(x.target,ast.Name):
                    fields.append(x.target.id)
                elif isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    lines.append(f"    [METHOD] {x.name}({', '.join(args(x))})")
            if fields: lines.append(f"    [FIELDS] {fields}")
        elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            lines.append(f"  [FUNCTION] {n.name}({', '.join(args(n))})")

OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
assert any("OpportunityOperatingSystem" in x for x in lines)
assert any("OpportunityPipeline" in x for x in lines)
assert any("OpportunityRankingEngine" in x for x in lines)
assert any("OpportunityValidationEngine" in x for x in lines)
print(f"[AUDIT] {OUT}")
print("[PASS] existing OOS semantic contracts physically captured")
print("[PASS] read_only=True execution_authority=FALSE")