
from qseries_v2.oracle_source_network.certification.sports_persistence_replay_gate import certify_replay
r=certify_replay()
print("[REPLAY]",r)
assert r.same_identity is True
assert r.first_id==r.replay_id
assert r.exact_readback>=1
assert r.execution_authority is False
print("[PASS] identical sports replay preserves canonical observation identity")
print("[PASS] duplicate replay remains exactly readable")
print("[PASS] OSN-064 sports persistence idempotency gate certified")
