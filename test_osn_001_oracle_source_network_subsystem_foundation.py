from pathlib import Path
from qseries_v2.oracle_source_network.foundation import descriptor, REVISION

d = descriptor()
assert REVISION == "OSN_001_ORACLE_SOURCE_NETWORK_SUBSYSTEM_FOUNDATION_V1"
assert d.subsystem == "OSN"
assert d.execution_authority is False
assert d.venue_neutral is True
assert d.upstream_control_plane == ("OAD-414","OAD-415","OAD-416","OAD-417","OAD-418")
assert len(d.fingerprint()) == 64

base = Path("qseries_v2/oracle_source_network")
for name in ("contracts","providers","canonical","acquisition","mapping","persistence","health","certification"):
    assert (base/name/"__init__.py").exists()

print("[PASS] OSN-001 subsystem foundation certified")
