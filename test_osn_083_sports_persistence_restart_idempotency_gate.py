
from pathlib import Path
from qseries_v2.oracle_source_network.certification.sports_persistence_restart_idempotency_gate import run_gate

result,state=run_gate(root=Path.cwd(),league="NHL")
print("[RESTART_IDEMPOTENCY]",result)
assert result.replay_resubmitted is False
assert result.replay_action=="READ_BEFORE_WRITE_HIT"
assert result.exact_readback>0
assert result.execution_authority is False
print("[STATE]",state)
print("[PASS] canonical identity stable across replay")
print("[PASS] durable row detected before write")
print("[PASS] duplicate resubmission prevented")
print("[PASS] OSN-083 restart idempotency certified")
