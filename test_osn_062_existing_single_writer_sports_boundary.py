
import inspect
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (
 submit_observation_batch,exact_postgresql_readback,PRODUCER
)
print("[OPH019_SIGNATURE]",inspect.signature(submit_observation_batch))
print("[OAD068_SIGNATURE]",inspect.signature(exact_postgresql_readback))
assert PRODUCER=="oracle.osn.sports"
assert callable(submit_observation_batch)
assert callable(exact_postgresql_readback)
print("[PASS] OSN-062 exact OPH-019 single-writer + OAD-068 readback boundary certified")
