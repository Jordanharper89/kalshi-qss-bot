from pathlib import Path
import ast,importlib.util

ROOT=Path.cwd()
OLR=ROOT/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
O4=ROOT/"qseries_v2/oracle_learning_runtime/olr_004_learning_cycle_state.py"
for p in (OLR,O4):
    assert p.exists(),f"MISSING:{p}"
    ast.parse(p.read_text(encoding="utf-8"))
    print("[PASS] parses:",p.as_posix())

olr=OLR.read_text(encoding="utf-8")
tree=ast.parse(olr)
imports=[]
for n in ast.walk(tree):
    if isinstance(n,ast.ImportFrom):
        imports.append((n.module or "",[a.name for a in n.names]))
print("[OLR009_IMPORTS]")
for m,n in imports:
    if "slop" in m.lower() or "olr_004" in m.lower(): print(" ",m,",".join(n))

slopmods=[m for m,n in imports if "slop_069" in m.lower()]
assert slopmods,"SLOP069_IMPORT_NOT_FOUND_IN_OLR009"
spec=importlib.util.find_spec(slopmods[0])
assert spec and spec.origin,"SLOP069_IMPORTED_MODULE_NOT_RESOLVABLE"
S69=Path(spec.origin)
print("[SLOP069_RESOLVED]",S69.as_posix())
s69=S69.read_text(encoding="utf-8")
ast.parse(s69)

t4=ast.parse(O4.read_text(encoding="utf-8"))
mods=[]
for n in ast.walk(t4):
    if isinstance(n,ast.ImportFrom) and n.module: mods.append(n.module)
print("[OLR004_IMPORTS]")
for m in mods: print(" ",m)

terms=("input_hash","event_hash","source_hash","applied_through_sequence","seen","dedup","duplicate")
hits={}
for m in mods:
    if not m.startswith("qseries_v2."): continue
    sp=importlib.util.find_spec(m)
    if not sp or not sp.origin or not sp.origin.endswith(".py"): continue
    p=Path(sp.origin); txt=p.read_text(encoding="utf-8")
    h=[x for x in terms if x in txt]
    if h:
        hits[p.as_posix()]=h
        print("[OCL_MODULE]",p.as_posix(),"HITS=",",".join(h))
print("[RECOVERY] identity_evidence=",any(any(x in h for x in ("input_hash","event_hash","source_hash","seen","dedup","duplicate")) for h in hits.values()))
print("[RECOVERY] sequence_evidence=",any("applied_through_sequence" in h for h in hits.values()))
print("[SLOP069] synthetic_cursor_literal=","SLOP:BUY_PRESSURE" in s69)
print("[SLOP069] consumption_logic=","consum" in s69.lower())
print("[PASS] SLOP-073B targeted import-resolved audit complete")
print("[INFO] read_only=True execution_authority=FALSE")
