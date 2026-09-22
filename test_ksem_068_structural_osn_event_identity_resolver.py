from pathlib import Path
from dataclasses import asdict
import json
from qseries_v2.kalshi_sports_evidence_mapping.structural_osn_event_identity_resolver import resolve_cohort

root = Path.cwd()
src = json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem067_structural_kalshi_event_identity.json").read_text(encoding="utf-8"))
rows, events = resolve_cohort(src["rows"], root=root, timeout_seconds=15)
statuses = ("EXACT_BOUND","PARTIAL","AMBIGUOUS","SOURCE_GAP","UNSUPPORTED")
counts = {s:sum(r.status==s for r in rows) for s in statuses}
print("[EVENT_COUNTS]", {k:len(v) for k,v in events.items()})
print("[COUNTS]", counts)
for r in rows[:20]:
    print("[BIND]",r.league,r.event_ticker,r.status,r.away_team,r.home_team,r.match_method)
assert rows
assert sum(counts.values()) == len(rows)
assert counts["EXACT_BOUND"] > 0, "no physical structural Kalshi event->OSN event exact binding"
state = root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem068_structural_osn_event_identity_binding.json").write_text(
    json.dumps({"rows":[asdict(r) for r in rows],"counts":counts,"event_counts":{k:len(v) for k,v in events.items()},"execution_authority":False},indent=2),
    encoding="utf-8"
)
print("[PASS] physical structural Kalshi event -> OSN canonical event binding proven")
print("[PASS] KSEM-068 certified")
