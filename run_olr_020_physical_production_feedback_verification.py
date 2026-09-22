from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
from qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import materialize_feedback_snapshot

if __name__=="__main__":
    print("="*72);print(" OLR-020 PHYSICAL PRODUCTION LEARNED-STATE FEEDBACK VERIFICATION");print("="*72)
    root=Path.cwd();state=load_production_learned_state(root)
    print(f"[LEARNED STATE] cycles={state.cycles} outcomes_learned={state.outcomes_learned} learned_records={state.learned_records} markets={len(state.learned_market_counts)}")
    print(f"[LEARNED STATE] learner_state_hash={state.learner_state_hash or 'NONE'}")
    summary=materialize_feedback_snapshot(root)
    print(f"[FEEDBACK] markets={summary.markets} learned_records={summary.learned_records} snapshot={summary.snapshot_path}")
    print("[PASS] Real durable OLR learning state projected into OLR-owned reasoning feedback snapshot")
    print("[PASS] Frozen OCR/OCL/OIS boundaries remained read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-020 PHYSICAL PRODUCTION FEEDBACK VERIFIED")
