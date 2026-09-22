from pathlib import Path
import json
from dataclasses import asdict
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_sports_proposition_context import reconstruct_rows

root=Path.cwd()
src=json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem061_exact_live_underlying_market_retrieval.json").read_text(encoding="utf-8"))
rows=reconstruct_rows(src["rows"])
ready=[x for x in rows if x.status=="READY"]
supported=[x for x in rows if x.league in ("NFL","NCAAF","NBA","NHL","MLS","EPL")]
print("[TOTAL]",len(rows)); print("[SUPPORTED]",len(supported)); print("[READY]",len(ready))
for x in rows[:12]:
    print("[CONTEXT]",x.market_ticker,x.league,x.proposition_type,x.status,x.title[:100])
assert rows
assert supported, "no exact current underlying market resolved into an admitted OSN league"
state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem062_exact_live_sports_proposition_context.json").write_text(
    json.dumps({"rows":[asdict(x) for x in rows],"supported":len(supported),"ready":len(ready),"execution_authority":False},indent=2),
    encoding="utf-8")
print("[PASS] exact current underlying sports proposition context reconstructed")
print("[PASS] KSEM-062 certified")
