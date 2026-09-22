from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture
from qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import commit_checkpoint_after_readback
from qseries_v2.oracle_source_network.certification.sports_restart_recovery_gate import recover_from_checkpoint

physical = persist_fixture(timeout_seconds=45.0)
print("[PHYSICAL]", physical)
assert physical.exact_readback >= 1

observed = datetime.now(timezone.utc).isoformat()
checkpoint = commit_checkpoint_after_readback(
    "NFL",
    physical.observation_id,
    observed,
    physical.exact_readback,
    root=Path.cwd(),
)
print("[CHECKPOINT]", checkpoint)

recovery = recover_from_checkpoint(
    "NFL",
    root=Path.cwd(),
    now=observed,
)
print("[RESTART_RECOVERY]", recovery)

assert recovery.checkpoint_found is True
assert recovery.checkpoint_observation_durable is True
assert recovery.replay_resubmitted is False
assert recovery.gap_seconds == 0
assert recovery.backfill_windows == 0
assert recovery.recovery_status == "RESUME_LIVE"
assert recovery.execution_authority is False

print("[PASS] restart reloaded durable sports checkpoint")
print("[PASS] checkpoint observation exact-readback verified before resume")
print("[PASS] already-durable observation not resubmitted")
print("[PASS] zero-gap restart resumes live safely")
print("[PASS] OSN-069 restart recovery physical gate certified")
