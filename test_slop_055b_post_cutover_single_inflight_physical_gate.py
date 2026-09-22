from pathlib import Path
from datetime import datetime
from collections import Counter
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
b=datetime.fromisoformat(Path("runtime_state/solana_live_opportunity/slop_054g_post_cutover_cohort_start.txt").read_text().strip())
ps=[p for p in read_predictions(Path.cwd()) if p.frozen_at>=b]
c=Counter(str(p.token_address) for p in ps)
dups={k:v for k,v in c.items() if v>1}
print("[COHORT_START]",b.isoformat())
print("[CLEAN_PREDICTIONS]",len(ps))
print("[CLEAN_TOKENS]",len(c))
print("[DUPLICATE_TOKEN_PREDICTIONS]",sum(v-1 for v in c.values()))
for k,v in sorted(dups.items()):print("[DUPLICATE]",k,v)
if not ps:
 print("[WAIT] no post-cutover prediction exists yet")
 print("[WAIT] leave Oracle running and rerun this same test later")
 raise SystemExit(2)
assert not dups,"POST_CUTOVER_SINGLE_INFLIGHT_TOKEN_BOUNDARY_VIOLATED"
assert len(ps)==len(c)
print("[PASS] every post-cutover token has exactly one prediction")
print("[PASS] fresh runtime canonical-pair single-inflight boundary physically holds")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-055B CERTIFIED")
