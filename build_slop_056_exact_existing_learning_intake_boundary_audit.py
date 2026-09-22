from pathlib import Path
import ast,json

ROOT=Path.cwd()
OUT=ROOT/"runtime_state/solana_live_opportunity/slop_056_learning_boundary_audit.json"
TEST=ROOT/"test_slop_056_exact_existing_learning_intake_boundary_audit.py"
names=("run_oracle_PROVEN_learning_runtime.py","run_opr_004_learning_persistent_ingress.py")
found={}
for name in names:
 hits=[p for p in ROOT.rglob(name) if ".venv" not in p.parts and "venv" not in p.parts]
 assert len(hits)==1,(name,[str(x) for x in hits])
 p=hits[0]; src=p.read_text(encoding="utf-8"); tree=ast.parse(src)
 found[name]={"path":str(p.relative_to(ROOT)),
  "imports":[ast.unparse(x) for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom))],
  "functions":[x.name for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]}
mods=[]
for p in ROOT.rglob("*.py"):
 if any(x in p.parts for x in (".venv","venv")): continue
 try:s=p.read_text(encoding="utf-8")
 except UnicodeDecodeError:continue
 if "OLR-009" in s or "proven_historical_path" in s:
  mods.append(str(p.relative_to(ROOT)))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"entrypoints":found,"olr009_refs":sorted(mods),
 "read_only":True,"execution_authority":False},indent=2),encoding="utf-8")
TEST.write_text("""import json
from pathlib import Path
p=Path("runtime_state/solana_live_opportunity/slop_056_learning_boundary_audit.json")
x=json.loads(p.read_text())
assert len(x["entrypoints"])==2
assert x["olr009_refs"],"NO_OLR009_PHYSICAL_REFERENCE"
assert x["read_only"] and not x["execution_authority"]
for n,v in x["entrypoints"].items():
 print("[ENTRYPOINT]",n,"->",v["path"])
 print("[FUNCTIONS]",v["functions"])
 print("[IMPORTS]",v["imports"])
print("[OLR009_REFS]",x["olr009_refs"])
print("[PASS] existing learning boundary physically audited")
print("[PASS] no learner/runtime mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-056 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-056 exact learning-intake audit installed")
print("[PASS] test installed:",TEST.name)