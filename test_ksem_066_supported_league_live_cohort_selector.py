from pathlib import Path
import json
from qseries_v2.kalshi_sports_evidence_mapping.supported_league_live_cohort import select_supported_live_cohort

root = Path.cwd()
rows = select_supported_live_cohort(root=root, universe_limit=1000, max_supported=40, timeout_seconds=15)
counts = {k: sum(r["status"] == k for r in rows) for k in ("RESOLVED","NOT_FOUND","ERROR")}
leagues = {}
for r in rows:
    leagues[r["league_hint"]] = leagues.get(r["league_hint"], 0) + 1
print("[ROWS]", len(rows))
print("[LEAGUES]", leagues)
print("[COUNTS]", counts)
for r in rows[:15]:
    print("[SUPPORTED]", r["league_hint"], r["market_ticker"], r["status"])
assert rows, "no admitted six-league underlying legs present in bounded live universe"
assert counts["RESOLVED"] > 0, "no admitted six-league underlying market resolved exactly"
assert counts["ERROR"] == 0, f"exact retrieval errors present: {counts}"
state = root/"qseries_v2/kalshi_sports_evidence_mapping/state"
state.mkdir(parents=True, exist_ok=True)
(state/"ksem066_supported_league_live_cohort.json").write_text(
    json.dumps({"rows": rows, "counts": counts, "leagues": leagues, "execution_authority": False}, indent=2, default=str),
    encoding="utf-8"
)
print("[PASS] admitted six-league live cohort selected before exact retrieval")
print("[PASS] KSEM-066 certified")
