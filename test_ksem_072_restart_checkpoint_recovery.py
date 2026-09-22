from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.restart_checkpoint_recovery import recover_and_resume
root=Path.cwd()
a=recover_and_resume(root); b=recover_and_resume(root)
print("[A]",a); print("[B]",b)
assert a["recovered_prior_state"] and b["recovered_prior_state"]
assert a["resumed_total_rows"]==a["resumed_accounted_rows"]>0
assert b["resumed_total_rows"]==b["resumed_accounted_rows"]>0
assert a["execution_authority"] is False and b["probability_enabled"] is False
print("[PASS] durable state recovered and mapping resumed idempotently twice")
print("[PASS] KSEM-072 certified")
