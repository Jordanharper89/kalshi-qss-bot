import inspect

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    submit_observation_batch,
    await_request,
)
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback
from qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture

print("[OPH019_SUBMIT_SIGNATURE]", inspect.signature(submit_observation_batch))
print("[OPH019_AWAIT_SIGNATURE]", inspect.signature(await_request))
print("[OAD068_SIGNATURE]", inspect.signature(exact_postgresql_readback))

result = persist_fixture(timeout_seconds=45.0)
print("[PHYSICAL_COMMIT_AWAIT]", result)

assert len(result.request_id) >= 8
assert len(result.observation_id) >= 32
assert result.committed_events >= 1
assert result.exact_readback >= 1
assert result.execution_authority is False

print("[PASS] certified OPH-021 writer runner activated/available")
print("[PASS] OPH-019 request awaited through terminal commit state")
print("[PASS] sports observation committed before readback")
print("[PASS] exact PostgreSQL observation-ID readback certified")
print("[PASS] OSN-063 commit-await physical rebuild certified")
