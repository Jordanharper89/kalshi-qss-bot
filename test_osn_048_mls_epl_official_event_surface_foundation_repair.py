
from qseries_v2.oracle_source_network.acquisition.soccer_event_surface_boundary import states

rows=states()
for r in rows:
    print("[BOUNDARY]",r)
assert tuple(r.league for r in rows)==("MLS","EPL")
assert all(r.production_event_admitted is False for r in rows)
assert all(r.execution_authority is False for r in rows)
assert rows[0].observed_role=="SCHEDULE_ANNOUNCEMENT_ARTICLE"
assert rows[1].observed_role=="FIXTURE_ANNOUNCEMENT_ARTICLE"
print("[PASS] MLS + EPL article surfaces explicitly removed from production event admission")
print("[PASS] OSN-048 MLS + EPL official event-surface foundation repair certified")
