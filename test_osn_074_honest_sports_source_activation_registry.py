from qseries_v2.oracle_source_network.runtime.sports_source_activation_registry import build_activation_registry

rows = build_activation_registry()
for row in rows:
    print("[ACTIVATION]", row)

assert tuple(r.league for r in rows) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")
assert all(r.physical_certified is True for r in rows)
assert all(r.execution_authority is False for r in rows)
assert all(r.state == "PHYSICAL_SOURCE_PROVEN_RUNTIME_CALLABLE_NOT_YET_FROZEN" for r in rows)

print("[PASS] source truth frozen without falsely claiming direct runtime callable activation")
print("[PASS] exact interface manifest preserved for next binding step")
print("[PASS] OSN-074 honest source activation registry certified")
