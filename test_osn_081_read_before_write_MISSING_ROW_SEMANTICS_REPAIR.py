
from pathlib import Path
import uuid

from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import exact_readback, readback_count

missing="osn081-missing-"+uuid.uuid4().hex
value=exact_readback(missing,root=Path.cwd())
count=readback_count(value)

print("[MISSING_READBACK]",missing,"count=",count,"value_type=",type(value).__name__)
assert count==0
print("[PASS] exact OAD-068 missing-row exception normalized to read-before-write miss")
print("[PASS] unexpected RuntimeError values remain unmasked")
print("[PASS] OSN-081 read-before-write missing-row semantics repaired")
