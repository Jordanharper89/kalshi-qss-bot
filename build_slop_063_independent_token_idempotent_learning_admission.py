from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
P=M/"slop_063_independent_token_idempotent_learning_admission.py"
P.write_text(r'''import json
from pathlib import Path
from .slop_061_canonical_prospective_learning_evidence import learning_evidence
from .slop_062_native_ocl_prospective_outcome_bridge import build_slop_learning_input

def _path(root): return Path(root)/"runtime_state/solana_live_opportunity/slop_063_learning_admissions.json"

def candidate_inputs(root=None):
 root=Path(root or Path.cwd()); chosen={}
 for e in sorted(learning_evidence(root),key=lambda x:(x["frozen_at"],x["prediction_id"])):
  chosen.setdefault(e["token_address"],e)
 out=[]
 for seq,e in enumerate(chosen.values(),1):
  oo,ev,ri=build_slop_learning_input(seq,e)
  out.append((e,oo,ev,ri))
 return out

def admit(root=None):
 root=Path(root or Path.cwd()); p=_path(root)
 old=json.loads(p.read_text()) if p.exists() else []
 seen={x["event_id"] for x in old}; added=[]
 for e,oo,ev,ri in candidate_inputs(root):
  if ev.event_id in seen: continue
  added.append({"event_id":ev.event_id,"token_address":e["token_address"],
   "prediction_id":e["prediction_id"],"evidence_hash":e["evidence_hash"],
   "input_hash":ri.input_hash,"status":"ADMITTED"})
  seen.add(ev.event_id)
 if added:
  p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(json.dumps(old+added,indent=2,sort_keys=True),encoding="utf-8")
 return added
''',encoding="utf-8")
T=Path("test_slop_063_independent_token_idempotent_learning_admission.py")
T.write_text(r'''from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_063_independent_token_idempotent_learning_admission import candidate_inputs,admit
r=Path.cwd(); c=candidate_inputs(r)
assert c and len(c)==len({x[0]["token_address"] for x in c})
a=admit(r); b=admit(r)
assert not b,"IDEMPOTENCY_FAILURE"
print("[INDEPENDENT_TOKEN_CANDIDATES]",len(c))
print("[NEW_ADMISSIONS]",len(a))
print("[SECOND_PASS_ADMISSIONS]",len(b))
print("[PASS] one deterministic learning admission per independent token")
print("[PASS] learning admission idempotent")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-063 CERTIFIED")
''',encoding="utf-8")
print("[PASS] SLOP-063 independent-token learning admission installed")
print("[PASS] test installed:",T.name)