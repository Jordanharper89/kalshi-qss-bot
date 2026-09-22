import inspect

from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (
    submit_observation_batch,
    exact_postgresql_readback,
    WRITER_ID,
)
from qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture

print("[OPH019_SIGNATURE]", inspect.signature(submit_observation_batch))
print("[OAD068_SIGNATURE]", inspect.signature(exact_postgresql_readback))

assert str(inspect.signature(submit_observation_batch)) == "(writer_id, priority, observations, root=None)"
assert str(inspect.signature(exact_postgresql_readback)) == "(observation_ids, root=None)"
assert WRITER_ID == "oracle.osn.sports"

r = persist_fixture()
print("[PHYSICAL_REPAIR]", r)

assert r.writer_id == "oracle.osn.sports"
assert len(r.observation_id) >= 32
assert r.exact_readback >= 1
assert r.execution_authority is False

print("[PASS] exact OPH-019 writer_id contract used")
print("[PASS] sports observation persisted through existing single writer")
print("[PASS] exact PostgreSQL observation-ID readback certified")
print("[PASS] OSN-063 writer_id repair certified")
