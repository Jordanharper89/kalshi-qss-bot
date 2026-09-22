
from qseries_v2.oracle_source_network.acquisition.nhl_event_surface_boundary import current_boundary,validate_official_candidate

b=current_boundary()
print("[BOUNDARY]",b)
assert b.event_surface_required is True
assert b.production_event_admitted is False
assert b.execution_authority is False
assert b.page_surface_status=="HTML_SHELL_NO_EVENT_OBJECTS_PROVEN"
assert validate_official_candidate("https://www.nhl.com/schedule")
assert not validate_official_candidate("https://example.com/schedule")
print("[PASS] OSN-047 retired NHL HTML shell as production event surface")
print("[PASS] OSN-047 NHL official event-surface foundation repair certified")
