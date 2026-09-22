from pathlib import Path
import ast

root=Path.cwd()

targets=[
    root/"qseries_v2/oracle_adapters/independent/oad_230_crypto_causal_narrative_physical_resolution.py",
    root/"qseries_v2/oracle_continuous_learner/ocl_014_causal_evidence.py",
]

for p in targets:
    assert p.exists(),p
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)
    funcs=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    print("[FILE]",p.as_posix())
    print("[FUNCTIONS]",funcs)

    for token in (
        "causal_state_hash",
        "HOLD_EXPLICIT_CAUSAL_EVIDENCE_REQUIRED",
        "causal",
    ):
        hits=[x.strip() for x in src.splitlines() if token.lower() in x.lower()]
        print("[TOKEN]",token,"hits=",len(hits))
        for x in hits[:20]:
            print(" ",x[:240])

matches=[]
for p in (root/"qseries_v2").rglob("*.py"):
    try:
        src=p.read_text(encoding="utf-8")
    except Exception:
        continue
    if "causal_state_hash" in src:
        matches.append(p.as_posix())

print("[CAUSAL_STATE_HASH_FILES]",len(matches))
for x in matches:
    print("[CAUSAL_FILE]",x)

print("[PASS] OPA-006 causal state physical code-path audit complete")
