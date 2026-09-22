
from qseries_v2.oracle_source_network.certification.sports_source_truth import SOURCES, production_ready, blocked

assert len(SOURCES) == 8
assert len(production_ready()) == 7
assert len(blocked()) == 1
assert blocked()[0].league == "UCL"
assert all(x.execution_authority is False for x in SOURCES)
print("[PASS] production_ready_leagues=", tuple(x.league for x in production_ready()))
print("[PASS] blocked_leagues=", tuple(x.league for x in blocked()))
print("[PASS] OSN-024 physical sports source truth registry certified")
