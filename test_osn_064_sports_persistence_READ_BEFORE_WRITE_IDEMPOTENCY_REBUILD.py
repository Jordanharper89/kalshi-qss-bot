from qseries_v2.oracle_source_network.certification.sports_persistence_replay_gate import certify_replay

result = certify_replay(timeout_seconds=45.0)
print("[READ_BEFORE_WRITE_REPLAY]", result)

assert len(result.observation_id) >= 32
assert len(result.first_request_id) >= 8
assert result.first_committed_events >= 1
assert result.replay_already_present is True
assert result.replay_resubmitted is False
assert result.exact_readback >= 1
assert result.execution_authority is False

print("[PASS] first sports observation committed through existing single writer")
print("[PASS] replay canonicalized to identical observation identity")
print("[PASS] duplicate identity detected by exact PostgreSQL read-before-write")
print("[PASS] duplicate identity was not resubmitted")
print("[PASS] durable exact readback remains available")
print("[PASS] OSN-064 read-before-write idempotency rebuild certified")
