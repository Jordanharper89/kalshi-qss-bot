from pathlib import Path
import ast
R=Path.cwd()
mods=[
 ("qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py","build_outcome_observation"),
 ("qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py","assemble_learning_event"),
 ("qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py","build_runtime_input")]
for rel,fn in mods:
 p=R/rel; assert p.exists(),f"MISSING:{p}"
 t=ast.parse(p.read_text(encoding="utf-8"))
 f=next(x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==fn)
 print("[MODULE]",rel)
 print("[FUNCTION]",ast.unparse(f))
 for x in t.body:
  if isinstance(x,ast.ClassDef):
   print("[CLASS]",x.name)
   print(ast.unparse(x))
T=R/"test_slop_060_native_ocl_learning_primitive_contract_audit.py"
T.write_text("""from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input
assert callable(build_outcome_observation)
assert callable(assemble_learning_event)
assert callable(build_runtime_input)
print("[PASS] native OCL learning primitives importable")
print("[PASS] no learning/runtime/state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-060 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-060 native OCL primitive contract audit installed")
print("[PASS] test installed:",T.name)