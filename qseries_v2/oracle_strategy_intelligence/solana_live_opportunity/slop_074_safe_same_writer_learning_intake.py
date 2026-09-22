from pathlib import Path
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
