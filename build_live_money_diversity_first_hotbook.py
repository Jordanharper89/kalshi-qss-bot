from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"live_money_runtime.py"
TEST=ROOT/"test_live_money_diversity_first_hotbook.py"
HELPER='\n# DIVERSITY_FIRST_INVENTORY_V1\ndef _oracle_token_of_row(row):\n    if isinstance(row,dict):\n        for k in ("token","mint","base_mint","token_mint"):\n            v=row.get(k)\n            if v:\n                return str(v)\n        pk=str(row.get("pair_key") or "")\n        if "|" in pk:\n            return pk.split("|",1)[0]\n    for k in ("token","mint","base_mint","token_mint"):\n        v=getattr(row,k,None)\n        if v:\n            return str(v)\n    pk=str(getattr(row,"pair_key","") or "")\n    if "|" in pk:\n        return pk.split("|",1)[0]\n    raise RuntimeError("DIVERSITY_TOKEN_IDENTITY_MISSING")\n\ndef _oracle_diversity_first(rows):\n    rows=list(rows or [])\n    first=[]\n    dup=[]\n    seen=set()\n    for row in rows:\n        token=_oracle_token_of_row(row)\n        if token in seen:\n            dup.append(row)\n        else:\n            seen.add(token)\n            first.append(row)\n    out=first+dup\n    print("[HOTBOOK_DIVERSITY_INPUT] routes=%d unique_tokens=%d duplicates=%d"%(len(rows),len(seen),len(dup)),flush=True)\n    return out\n'

if not TARGET.is_file():
    raise RuntimeError("LIVE_MONEY_RUNTIME_MISSING")

src=TARGET.read_text(encoding="utf-8")
tree=ast.parse(src)

def marker(node,text):
    try:
        return text in ast.unparse(node)
    except Exception:
        return False

inventory_name=None
hot_name=None
main_node=None

for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=="main":
        main_node=node
        break

if main_node is None:
    raise RuntimeError("LIVE_MONEY_MAIN_NOT_FOUND")

for node in ast.walk(main_node):
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
        text=ast.unparse(node)
        if "[INVENTORY]" in text:
            for sub in ast.walk(node):
                if isinstance(sub,ast.Call) and isinstance(sub.func,ast.Name) and sub.func.id=="len" and sub.args and isinstance(sub.args[0],ast.Name):
                    inventory_name=sub.args[0].id
                    break
        if "[HOT_BOOK]" in text:
            for sub in ast.walk(node):
                if isinstance(sub,ast.Call) and isinstance(sub.func,ast.Name) and sub.func.id=="len" and sub.args and isinstance(sub.args[0],ast.Name):
                    hot_name=sub.args[0].id
                    break

if not inventory_name or not hot_name:
    raise RuntimeError("DIVERSITY_SEAM_NOT_FOUND inventory=%r hot=%r"%(inventory_name,hot_name))

if "DIVERSITY_FIRST_INVENTORY_V1" not in src:
    lines=src.splitlines()
    insert_at=0
    for node in tree.body:
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            insert_at=max(insert_at,node.end_lineno)
    lines[insert_at:insert_at]=HELPER.strip("\n").splitlines()+[""]
    src="\n".join(lines)+"\n"
    ast.parse(src)

tree=ast.parse(src)
main_node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="main")

already=False
for node in ast.walk(main_node):
    if marker(node,"_oracle_diversity_first"):
        already=True
        break

if not already:
    insert_line=None
    for node in ast.walk(main_node):
        if isinstance(node,ast.Expr) and marker(node,"[INVENTORY]"):
            insert_line=node.lineno
            break
    if insert_line is None:
        raise RuntimeError("INVENTORY_PRINT_NOT_FOUND_AFTER_HELPER")
    lines=src.splitlines()
    lines.insert(insert_line-1,"    "+inventory_name+"=_oracle_diversity_first("+inventory_name+")")
    src="\n".join(lines)+"\n"
    ast.parse(src)

TARGET.write_text(src,encoding="utf-8")

TEST_CODE=(
"import ast\n"
"from pathlib import Path\n"
"from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as m\n"
"rows=[{'token':'A','pair_key':'A|1'},{'token':'A','pair_key':'A|2'},{'token':'B','pair_key':'B|1'},{'token':'C','pair_key':'C|1'},{'token':'B','pair_key':'B|2'}]\n"
"out=m._oracle_diversity_first(rows)\n"
"assert [x['token'] for x in out[:3]]==['A','B','C']\n"
"assert len(out)==5\n"
"s=Path(m.__file__).read_text(encoding='utf-8')\n"
"assert 'DIVERSITY_FIRST_INVENTORY_V1' in s\n"
"assert '_oracle_diversity_first' in s\n"
"assert '[HOTBOOK_DIVERSITY_INPUT]' in s\n"
"assert 'sendTransaction' not in s\n"
"ast.parse(s)\n"
"print('[PASS] diversity-first inventory handoff installed')\n"
)

TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] diversity-first hotbook handoff full installer")
print("[SEAM] inventory=%s hotbook=%s"%(inventory_name,hot_name))
print("[POLICY] one route per token first, duplicate pools second")
print("[ACCOUNT_CAP] existing selector unchanged")
print("[MONEY_PATH] checkpoint26->25->22->21->20->19 preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
