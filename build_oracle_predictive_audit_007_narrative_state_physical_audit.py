from pathlib import Path

ROOT=Path.cwd()
TEST=ROOT/"test_oracle_predictive_audit_007_narrative_state_physical_audit.py"

BODY=r'''
from pathlib import Path
import ast

root=Path.cwd()

targets=[
    root/"qseries_v2/oracle_adapters/independent/oad_230_crypto_causal_narrative_physical_resolution.py",
    root/"qseries_v2/oracle_continuous_learner/ocl_018_narrative_learning.py",
    root/"qseries_v2/oracle_continuous_learner/ocl_019_narrative_market_relationship.py",
]

for p in targets:
    assert p.exists(),p
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)
    funcs=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    print("[FILE]",p.as_posix())
    print("[FUNCTIONS]",funcs)

    for token in (
        "narrative_state_hash",
        "HOLD_EXPLICIT_NARRATIVE_EVIDENCE_REQUIRED",
        "narrative",
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
    if "narrative_state_hash" in src:
        matches.append(p.as_posix())

print("[NARRATIVE_STATE_HASH_FILES]",len(matches))
for x in matches:
    print("[NARRATIVE_FILE]",x)

print("[PASS] OPA-007 narrative state physical code-path audit complete")
'''

def main():
    print("="*120)
    print(" OPA-007 NARRATIVE STATE PHYSICAL AUDIT INSTALLER")
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",TEST.name)
    print("[PASS] no production mutation")

if __name__=="__main__":
    main()