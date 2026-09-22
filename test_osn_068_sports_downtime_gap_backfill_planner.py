from qseries_v2.oracle_source_network.runtime.sports_gap_backfill_plan import plan_gap_backfill

same = plan_gap_backfill(
    "NFL",
    "2026-09-05T20:00:00+00:00",
    "2026-09-05T20:00:00+00:00",
)
print("[NO_GAP]", same)
assert same.continuity_status == "CONTIGUOUS"
assert same.windows == ()

gap = plan_gap_backfill(
    "NFL",
    "2026-09-05T20:00:00+00:00",
    "2026-09-05T20:17:00+00:00",
    max_window_seconds=300,
)
print("[GAP]", gap)
assert gap.gap_seconds == 1020
assert gap.continuity_status == "BACKFILL_REQUIRED"
assert len(gap.windows) == 4
assert gap.windows[0].start == "2026-09-05T20:00:00+00:00"
assert gap.windows[-1].end == "2026-09-05T20:17:00+00:00"
assert gap.execution_authority is False

print("[PASS] zero-gap continuity detected")
print("[PASS] downtime gap split into bounded backfill windows")
print("[PASS] no unrecoverable time silently discarded")
print("[PASS] OSN-068 sports gap/backfill planner certified")
