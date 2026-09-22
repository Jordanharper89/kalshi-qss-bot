from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
OLR=ROOT/"qseries_v2"/"oracle_learning_runtime"/"olr_009_high_coverage_learning_cycle.py"
S069=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_live_opportunity"/"slop_069_existing_olr004_state_transition_integration.py"
assert STATE.exists(), "PRODUCTION_LEARNER_STATE_MISSING"
d=json.loads(STATE.read_text(encoding="utf-8"))
ocl=d.get("ocl_state",{})
print("[STATE] cycles=",d.get("cycles"))
print("[STATE] outcomes_learned=",d.get("outcomes_learned"))
print("[STATE] applied_through_sequence=",ocl.get("applied_through_sequence"))
print("[STATE] last_settlement_ts=",d.get("last_settlement_ts"))
print("[STATE] last_ticker=",d.get("last_ticker"))
ticker=str(d.get("last_ticker") or "")
corrupt=ticker=="SLOP:BUY_PRESSURE"
print("[CURSOR] synthetic_slop_cursor=",corrupt)
olr=OLR.read_text(encoding="utf-8") if OLR.exists() else ""
s69=S069.read_text(encoding="utf-8") if S069.exists() else ""
unsafe_import="slop_069" in olr.lower()
unsafe_call="apply_pending_slop" in olr
synthetic='"SLOP:BUY_PRESSURE"' in s69 or "'SLOP:BUY_PRESSURE'" in s69
print("[DISK] olr009_slop069_reference=",unsafe_import)
print("[DISK] olr009_apply_pending_slop_call=",unsafe_call)
print("[DISK] slop069_synthetic_cursor_literal=",synthetic)
if corrupt:
    print("[FAIL] LIVE_LEARNER_CURSOR_CORRUPTED_BY_SLOP")
elif unsafe_import or unsafe_call or synthetic:
    print("[BLOCK] LIVE_STATE_NOT_CURRENTLY_SYNTHETIC_BUT_UNSAFE_CUTOVER_REMAINS_ON_DISK")
else:
    print("[PASS] NO_SYNTHETIC_CURSOR_AND_NO_UNSAFE_CUTOVER_SIGNATURE")
print("[INFO] READ_ONLY_DIAGNOSTIC execution_authority=FALSE")
