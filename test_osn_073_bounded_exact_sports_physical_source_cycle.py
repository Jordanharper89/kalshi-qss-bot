from qseries_v2.oracle_source_network.certification.exact_sports_physical_source_cycle import run_source_cycle

rows = run_source_cycle(per_source_timeout=35)
assert tuple(r.league for r in rows) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")
assert all(r.passed for r in rows), rows
assert all(r.execution_authority is False for r in rows)
assert all((r.event_lines + r.physical_lines) >= 1 for r in rows), rows

print("[PASS] six admitted sports sources physically executed under hard timeout")
print("[PASS] each source produced physical/extraction evidence")
print("[PASS] no held or blocked league executed")
print("[PASS] OSN-073 bounded physical source cycle certified")
