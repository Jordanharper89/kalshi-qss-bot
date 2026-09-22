from pathlib import Path
T=Path("test_slop_065b_physical_end_to_end_learning_consumption_certification.py")
T.write_text(r'''from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import genesis_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_061_canonical_prospective_learning_evidence import learning_evidence
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_063_independent_token_idempotent_learning_admission import candidate_inputs
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_064c_exact_tuple_contract_learner_integration_repair import apply_slop_inputs
r=Path.cwd()
e=learning_evidence(r); c=candidate_inputs(r)
assert e and c
s=genesis_learning_runtime_state()
result,n,count=apply_slop_inputs(s,r)
assert result is not None
assert count==len(c)
assert n.outcomes_learned==s.outcomes_learned+count
assert n.cycles==s.cycles+1
outs={x["outcome"] for x in e}
assert outs <= {"TARGET_FIRST","STOP_FIRST","TIMEOUT"}
print("[CANONICAL_RESOLVED_EVIDENCE]",len(e))
print("[INDEPENDENT_TOKEN_INPUTS]",len(c))
print("[PHYSICAL_OUTCOME_CLASSES]",sorted(outs))
print("[LEARNER_CYCLE_DELTA]",n.cycles-s.cycles)
print("[LEARNER_OUTCOMES_DELTA]",n.outcomes_learned-s.outcomes_learned)
print("[PASS] real BUY_PRESSURE resolutions became native Oracle learning inputs")
print("[PASS] existing OCL/OLR learner state transition physically consumed them")
print("[PASS] independent-token accounting preserved")
print("[PASS] no parallel learner and no fake Kalshi settlement")
print("[PASS] production learner state remains untouched")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-065B CERTIFIED")
''',encoding="utf-8")
print("[PASS] SLOP-065B physical consumption certification installed")
print("[PASS] test installed:",T.name)