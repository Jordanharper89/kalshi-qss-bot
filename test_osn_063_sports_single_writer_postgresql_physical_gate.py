
from qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture
r=persist_fixture()
print("[PHYSICAL]",r)
assert r.exact_readback>=1
assert len(r.observation_id)>=32
assert r.execution_authority is False
print("[PASS] sports canonical observation persisted through OPH-019 single writer")
print("[PASS] exact PostgreSQL observation-ID readback certified")
print("[PASS] OSN-063 physical sports persistence gate certified")
