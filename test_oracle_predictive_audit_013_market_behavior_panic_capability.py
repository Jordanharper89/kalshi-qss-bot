from pathlib import Path
import ast
ROOT=Path.cwd()
targets=[ROOT/"qseries_v2/oracle_adapters/independent/oad_224_crypto_physical_market_behavior_state_materialization.py",ROOT/"qseries_v2/oracle_continuous_learner/ocl_011_market_behavior_observation.py",ROOT/"qseries_v2/oracle_continuous_learner/ocl_012_market_behavior_learning.py"]
tokens=("spread","bid","ask","liquidity","panic","velocity","momentum","reversal","overreaction","underreaction","dislocation","stale","volume","return","market_behavior_state_hash","evidence_hash","outcome_hash")
for p in targets:
    print("[TARGET]",p.as_posix(),"exists=",p.exists())
    if not p.exists():continue
    src=p.read_text(encoding="utf-8");tree=ast.parse(src)
    print("[FUNCTIONS]",[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))])
    for tok in tokens:
        hits=[x.strip() for x in src.splitlines() if tok.lower() in x.lower()]
        if hits:
            print("[CAPABILITY_TOKEN]",tok,"hits=",len(hits))
            for h in hits[:8]:print(" ",h[:240])
found=[]
for p in (ROOT/"qseries_v2").rglob("*.py"):
    try:s=p.read_text(encoding="utf-8").lower()
    except Exception:continue
    hits=[t for t in tokens[:-3] if t in s]
    if len(hits)>=3:found.append((p.as_posix(),hits))
print("[RELATED_MODULES]",len(found))
for p,h in found[:80]:print("[RELATED]",p,h)
print("[PASS] OPA-013 market behavior/panic capability audit complete")
