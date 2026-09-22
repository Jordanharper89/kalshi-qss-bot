from qseries_v2.oracle_source_network.certification.sports_persistence_replay_gate import certify_replay

result = certify_replay(timeout_seconds=45.0)
print("[REPLAY_COMMIT_AWAIT]", result)

assert result.same_identity is True
assert result.first_id == result.replay_id
assert len(result.first_request_id) >= 8
assert len(result.replay_request_id) >= 8
assert result.first_committed_events >= 1
assert result.replay_committed_events >= 1
assert result.exact_readback >= 1
assert result.execution_authority is False

print("[PASS] identical sports replay preserves canonical observation identity")
print("[PASS] first submission awaited through terminal commit state")
print("[PASS] replay submission awaited through terminal commit state")
print("[PASS] exact PostgreSQL readback succeeds after replay")
print("[PASS] OSN-064 commit-await replay rebuild certified")
