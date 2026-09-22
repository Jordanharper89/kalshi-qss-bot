
from pathlib import Path
from qseries_v2.oracle_source_network.certification.six_league_uniform_provider_gate import run_gate, ADMITTED

rows,state=run_gate(root=Path.cwd(),timeout=15)
assert tuple(r.league for r in rows)==ADMITTED
assert all(r.events>0 for r in rows)
assert all(r.unique_provider_ids>0 for r in rows)
assert all(r.execution_authority is False for r in rows)
print("[STATE]",state)
print("[PASS] NFL/NCAAF/NBA direct extractor paths physically reverified")
print("[PASS] NHL/MLS/EPL executable promoted production paths physically reverified")
print("[PASS] all six admitted leagues returned canonical provider identities")
print("[PASS] OSN-078 executable-foundation physical gate certified")
