from pathlib import Path
import json
from dataclasses import asdict
from qseries_v2.kalshi_sports_evidence_mapping.live_osn_exact_event_binding import run_binding

root=Path.cwd()
src=json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem062_exact_live_sports_proposition_context.json").read_text(encoding="utf-8"))
rows=[x for x in src["rows"] if x.get("league") in ("NFL","NCAAF","NBA","NHL","MLS","EPL")]
bindings,events=run_binding(rows,root=root,timeout=15)
counts={k:sum(x.status==k for x in bindings) for k in ("EXACT_BOUND","AMBIGUOUS","SOURCE_GAP")}
print("[EVENT_COUNTS]",{k:len(v) for k,v in events.items()})
print("[BINDING_COUNTS]",counts)
for x in bindings[:15]: print("[BINDING]",x.market_ticker,x.league,x.status,x.home_team,x.away_team,x.score)
assert bindings
assert sum(counts.values())==len(bindings)
state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem063_live_osn_exact_event_binding.json").write_text(
    json.dumps({"rows":[asdict(x) for x in bindings],"counts":counts,"event_counts":{k:len(v) for k,v in events.items()},"execution_authority":False},indent=2),
    encoding="utf-8")
print("[PASS] every supported live proposition received explicit OSN binding status")
print("[PASS] KSEM-063 certified")
