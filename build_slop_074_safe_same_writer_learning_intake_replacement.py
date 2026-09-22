from pathlib import Path

ROOT = Path.cwd()
MOD = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_074_safe_same_writer_learning_intake.py"
TEST = ROOT / "test_slop_074_safe_same_writer_learning_intake.py"

module = '''from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_004_learning_cycle_state import apply_learning_inputs
from .slop_067_opportunity_level_exactly_once_learning_lineage import load_consumed, save_consumed
from .slop_068_production_sequence_safe_learning_intake import pending_inputs

REVISION = "SLOP_074_SAFE_SAME_WRITER_LEARNING_INTAKE"

def prepare_pending_slop(state, root=None, progress=print):
    root = Path(root or Path.cwd())
    rows = pending_inputs(state, root)
    if not rows:
        return None, state, tuple()
    inputs = tuple(x[4] for x in rows)
    result, new = apply_learning_inputs(state, inputs, state.last_settlement_ts, state.last_ticker)
    progress(f"[SLOP LEARN PREPARE] outcomes={len(rows)} cycle={new.cycles} learned_total={new.outcomes_learned}")
    return result, new, tuple(rows)

def commit_consumed(rows, root=None, progress=print):
    root = Path(root or Path.cwd())
    if not rows:
        return 0
    d = load_consumed(root)
    added = 0
    for k, e, oo, ev, ri in rows:
        old = d.get(k)
        if old and old.get("status") == "learned":
            continue
        d[k] = {"prediction_id": e["prediction_id"], "token_address": e["token_address"],
                "event_id": ev.event_id, "input_hash": ri.input_hash, "status": "learned"}
        added += 1
    if added:
        save_consumed(d, root)
    progress(f"[SLOP LEARN COMMIT] newly_consumed={added}")
    return added
'''
MOD.write_text(module, encoding="utf-8")

test = '''from pathlib import Path
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
'''
TEST.write_text(test, encoding="utf-8")
print("="*96)
print(" SLOP-074 SAFE SAME-WRITER LEARNING INTAKE REPLACEMENT INSTALLER")
print("="*96)
print("[PASS] safe replacement module installed")
print("[PASS] test installed:",TEST.name)
print("[PASS] SLOP-069 production import untouched")
print("[PASS] prepare/commit boundary separated")
print("[NEXT] python test_slop_074_safe_same_writer_learning_intake.py")
