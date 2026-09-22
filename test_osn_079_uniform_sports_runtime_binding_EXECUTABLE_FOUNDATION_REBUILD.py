
from pathlib import Path
from qseries_v2.oracle_source_network.runtime.uniform_sports_runtime_bindings import freeze

rows,state=freeze(root=Path.cwd())
for r in rows:
    print("[BINDING]",r)

assert len(rows)==6
assert all(r.direct_runtime_callable_bound for r in rows)
assert all(r.physical_gate_certified for r in rows)
assert all(r.terminal_dependency=="NONE" for r in rows)
assert all(r.execution_authority is False for r in rows)

print("[STATE]",state)
print("[PASS] one physically proven runtime callable frozen for all six admitted leagues")
print("[PASS] obsolete reachability-only NHL/MLS/EPL callables are not runtime authority")
print("[PASS] terminal_dependency=NONE")
print("[PASS] OSN-079 executable-foundation runtime binding certified")
