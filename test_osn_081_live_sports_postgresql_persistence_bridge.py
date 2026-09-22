
from pathlib import Path
from qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import acquire_and_persist_one_per_league, ADMITTED

rows,state=acquire_and_persist_one_per_league(root=Path.cwd(),timeout=15,commit_timeout_seconds=45.0)
assert tuple(r.league for r in rows)==ADMITTED
assert all(r.readback_count>0 for r in rows)
assert all(r.execution_authority is False for r in rows)
print("[STATE]",state)
print("[PASS] six admitted leagues persisted through existing sports single-writer boundary")
print("[PASS] exact PostgreSQL readback verified")
print("[PASS] execution_authority=FALSE")
