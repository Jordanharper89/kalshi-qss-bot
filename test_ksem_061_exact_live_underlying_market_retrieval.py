from pathlib import Path
import json
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_underlying_market_retrieval import run_physical_gate

root=Path.cwd()
rows=run_physical_gate(root=root,max_tickers=25,timeout_seconds=15)
counts={k:sum(r["status"]==k for r in rows) for k in ("RESOLVED","NOT_FOUND","ERROR")}
print("[ROWS]",len(rows))
print("[COUNTS]",counts)
for r in rows[:10]:
    print("[SAMPLE]",r["market_ticker"],r["status"])
assert rows
assert counts["RESOLVED"]>0, "no current MVE underlying ticker resolved through exact Kalshi GET"
assert counts["ERROR"]==0, f"transport errors present: {counts}"
state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
state.mkdir(parents=True,exist_ok=True)
(state/"ksem061_exact_live_underlying_market_retrieval.json").write_text(
    json.dumps({"rows":rows,"counts":counts,"execution_authority":False},indent=2,default=str),
    encoding="utf-8")
print("[PASS] current MVE underlying markets physically resolved by exact ticker")
print("[PASS] KSEM-061 certified")
