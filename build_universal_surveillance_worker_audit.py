
from pathlib import Path
import ast

ROOT=Path.cwd()
FILES=[
    ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py",
    ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py",
]
OUT=ROOT/"UNIVERSAL_SURVEILLANCE_WORKER_AUDIT.txt"

def segment(src,node):
    lines=src.splitlines()
    return "\n".join(
        "%04d %s"%(i+1,lines[i])
        for i in range(node.lineno-1,node.end_lineno)
    )

wanted_names={
    "stable_shards",
    "truthful_worker",
    "_worker",
    "worker",
    "canonical_worker",
    "run_worker",
}

out=[]
for p in FILES:
    if not p.is_file():
        raise RuntimeError("MISSING:"+str(p))
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)
    out.append("="*120)
    out.append("FILE "+str(p.relative_to(ROOT)))
    found=0

    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            body=ast.unparse(node)
            interesting=(
                node.name in wanted_names
                or "websocket" in body.lower()
                or "subscribe" in body.lower()
                or "_shards" in body
                or "persistent._worker" in body
            )
            if interesting:
                out.append("--- FUNCTION %s L%d-L%d ---"%(node.name,node.lineno,node.end_lineno))
                out.append(segment(src,node))
                found+=1

    out.append("--- CALL SITES ---")
    lines=src.splitlines()
    for i,line in enumerate(lines):
        if any(x in line for x in (
            "persistent._worker",
            "merged._shards",
            "_worker(",
            "_shards(",
            "subscriptions=",
            "websocket",
            "accountSubscribe",
            "accountUnsubscribe",
        )):
            a=max(0,i-3); b=min(len(lines),i+4)
            out.extend("%04d %s"%(j+1,lines[j]) for j in range(a,b))

    out.append("[FUNCTIONS_CAPTURED] %d"%found)

OUT.write_text("\n".join(out)+"\n",encoding="utf-8")
print("[PASS] universal surveillance worker source capture")
print("[REPORT]",OUT)
print("[KEY] untouched")
print("[WALLET] untouched")
print("[RUNTIME] untouched")
print("[BROADCAST] untouched")
