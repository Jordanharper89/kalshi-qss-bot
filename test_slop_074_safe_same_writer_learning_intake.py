from pathlib import Path
import ast, hashlib
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import load_learning_runtime_state
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_074_safe_same_writer_learning_intake import prepare_pending_slop

ROOT=Path.cwd()
STATE=ROOT/"runtime_state/oracle_learning_runtime_state.json"
CONSUMED=ROOT/"runtime_state/solana_live_opportunity/slop_067_consumed_learning_lineage.json"
src=(ROOT/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_074_safe_same_writer_learning_intake.py").read_text(encoding="utf-8")
ast.parse(src)
assert "SLOP:BUY_PRESSURE" not in src
assert "state.last_settlement_ts" in src and "state.last_ticker" in src
before_state=hashlib.sha256(STATE.read_bytes()).hexdigest()
before_consumed=hashlib.sha256(CONSUMED.read_bytes()).hexdigest() if CONSUMED.exists() else None
state=load_learning_runtime_state(STATE)
result,new,rows=prepare_pending_slop(state,ROOT,progress=print)
after_state=hashlib.sha256(STATE.read_bytes()).hexdigest()
after_consumed=hashlib.sha256(CONSUMED.read_bytes()).hexdigest() if CONSUMED.exists() else None
assert before_state==after_state,"PRODUCTION_STATE_MUTATED"
assert before_consumed==after_consumed,"CONSUMED_LEDGER_MUTATED_DURING_PREPARE"
assert new.last_settlement_ts==state.last_settlement_ts
assert new.last_ticker==state.last_ticker
assert new.ocl_state.applied_through_sequence==state.ocl_state.applied_through_sequence+len(rows)
assert new.outcomes_learned==state.outcomes_learned+len(rows)
print("[PENDING_PREPARED]",len(rows))
print("[SEQUENCE_BEFORE]",state.ocl_state.applied_through_sequence)
print("[SEQUENCE_AFTER_SIMULATED]",new.ocl_state.applied_through_sequence)
print("[CURSOR_TS_PRESERVED]",new.last_settlement_ts)
print("[CURSOR_TICKER_PRESERVED]",new.last_ticker)
print("[PASS] native OLR-004 transition is in-memory during prepare")
print("[PASS] consumed ledger unchanged until explicit post-save commit")
print("[PASS] Kalshi cursor preserved exactly")
print("[PASS] production learner state unchanged")
print("[PASS] SLOP-074 CERTIFIED execution_authority=FALSE")
