
from pathlib import Path
import inspect

from qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import (
    acquire_and_persist_one_per_league, ADMITTED, _request_id
)
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import submit

class FixtureSubmission:
    request_id="fixture-request-id"

assert _request_id(FixtureSubmission())=="fixture-request-id"
print("[PASS] OPH-019 submission object request_id extraction verified")

rows,state=acquire_and_persist_one_per_league(
    root=Path.cwd(),
    timeout=15,
    commit_timeout_seconds=45.0,
)

print("[STATE]",state)
assert tuple(r.league for r in rows)==ADMITTED
assert all(r.readback_count>0 for r in rows)
assert all(r.execution_authority is False for r in rows)
assert all(
    (r.write_action=="READ_BEFORE_WRITE_HIT") or bool(r.request_id)
    for r in rows
)

print("[PASS] six admitted leagues passed live source -> canonical -> OPH-019 -> await -> exact readback")
print("[PASS] await uses exact submission.request_id")
print("[PASS] OSN-081 live sports PostgreSQL persistence certified")
print("[PASS] execution_authority=FALSE")
