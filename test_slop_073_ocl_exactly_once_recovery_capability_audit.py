from pathlib import Path
import ast,re

ROOT=Path.cwd()
FILES=[
ROOT/"qseries_v2/oracle_learning_runtime/olr_004_learning_cycle_state.py",
ROOT/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py",
ROOT/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_069_existing_olr004_state_transition_integration.py",
]
for p in FILES:
    assert p.exists(),f"MISSING:{p}"
    ast.parse(p.read_text(encoding="utf-8"))
    print("[PASS] parses:",p.as_posix())

p4=FILES[0].read_text(encoding="utf-8")
tree=ast.parse(p4)
imports=[]
for n in ast.walk(tree):
    if isinstance(n,ast.ImportFrom):
        imports.append((n.module or "",[a.name for a in n.names]))
    elif isinstance(n,ast.Import):
        imports.extend((a.name,[]) for a in n.names)
print("[OLR004_IMPORTS]")
for m,names in imports:
    print(" ",m,",".join(names))

mods=set()
for m,names in imports:
    if m.startswith("qseries_v2.") and ("oracle" in m.lower() or "ocl" in m.lower()):
        rel=ROOT/Path(*m.split("."))
        py=rel.with_suffix(".py")
        if py.exists(): mods.add(py)
        init=rel/"__init__.py"
        if init.exists(): mods.add(init)

terms=("input_hash","event_hash","source_hash","applied_through_sequence",
       "assemble_runtime_batch","run_learning_cycle","seen","dedup","duplicate")
found={}
for p in sorted(mods):
    txt=p.read_text(encoding="utf-8")
    hits=[t for t in terms if t in txt]
    if hits:
        found[p]=hits
        print("[OCL_MODULE]",p.as_posix(),"HITS=",",".join(hits))

identity_persisted=any(
    any(t in hits for t in ("input_hash","event_hash","source_hash","seen","dedup","duplicate"))
    for hits in found.values()
)
sequence_persisted=("applied_through_sequence" in p4) or any(
    "applied_through_sequence" in hits for hits in found.values()
)
print("[RECOVERY] identity_persistence_evidence=",identity_persisted)
print("[RECOVERY] sequence_checkpoint_evidence=",sequence_persisted)

s69=FILES[2].read_text(encoding="utf-8")
early=bool(re.search(r"(persist|save|write).*consum",s69,re.I)) or "consumed" in s69.lower()
print("[SLOP069] consumption_ledger_logic_present=",early)
print("[PASS] READ_ONLY targeted exactly-once recovery audit complete")
print("[INFO] No production files or runtime state mutated; execution_authority=FALSE")
