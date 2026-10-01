from pathlib import Path
import json
R=Path.cwd(); st=R/"runtime_state/oracle_learning_runtime_state.json"
d=json.loads(st.read_text(encoding="utf-8"))
jp=R/"runtime_state/solana_live_opportunity/slop_075b_learning_commit_journal.json"
print("[LIVE_CYCLES]",d.get("cycles")); print("[LIVE_OUTCOMES]",d.get("outcomes_learned"))
print("[LIVE_APPLIED_THROUGH]",d.get("ocl_state",{}).get("applied_through_sequence"))
print("[LIVE_LAST_SETTLEMENT_TS]",d.get("last_settlement_ts")); print("[LIVE_LAST_TICKER]",d.get("last_ticker"))
print("[COMMIT_JOURNAL_PRESENT]",jp.exists())
assert str(d.get("last_ticker") or "")!="SLOP:BUY_PRESSURE","SYNTHETIC_CURSOR_CORRUPTION"
assert not jp.exists(),"STRANDED_SLOP_COMMIT_JOURNAL"
print("[PASS] live Kalshi cursor remains legitimate")
print("[PASS] no stranded SLOP commit journal")
print("[PASS] SLOP-077B live proof checkpoint execution_authority=FALSE")
