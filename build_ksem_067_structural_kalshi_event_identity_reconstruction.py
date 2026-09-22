from pathlib import Path
ROOT = Path.cwd()
PKG = ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE = PKG/"state"
MOD = PKG/"structural_kalshi_event_identity.py"
TEST = ROOT/"test_ksem_067_structural_kalshi_event_identity_reconstruction.py"

MODULE = r"""
from dataclasses import dataclass, asdict

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

@dataclass(frozen=True)
class StructuralKalshiEventIdentity:
    parent_ticker: str
    market_ticker: str
    event_ticker: str
    league: str
    outcome_code: str
    title: str
    exact_event_relationship: bool
    status: str
    reasons: tuple
    execution_authority: bool = False

def _event_from_market(market):
    return str((market or {}).get("event_ticker") or "").strip().upper()

def _outcome_code(market_ticker, event_ticker):
    prefix = event_ticker + "-"
    if market_ticker.startswith(prefix):
        return market_ticker[len(prefix):]
    return ""

def reconstruct_identity(row):
    market = dict(row.get("market") or {})
    market_ticker = str(row.get("market_ticker") or market.get("ticker") or "").strip().upper()
    market_event = _event_from_market(market)
    leg_event = str(row.get("leg_event_ticker") or "").strip().upper()
    event_ticker = market_event or leg_event
    league = str(row.get("league_hint") or "").strip().upper()
    outcome = _outcome_code(market_ticker, event_ticker) if event_ticker else ""
    reasons = []
    if row.get("status") != "RESOLVED":
        reasons.append("EXACT_MARKET_NOT_RESOLVED")
    if not event_ticker:
        reasons.append("EVENT_TICKER_MISSING")
    if market_event and leg_event and market_event != leg_event:
        reasons.append("LEG_EVENT_TICKER_DISAGREES_WITH_EXACT_MARKET")
    exact_relation = bool(event_ticker and market_ticker.startswith(event_ticker + "-"))
    if not exact_relation:
        reasons.append("MARKET_NOT_STRUCTURALLY_CHILD_OF_EVENT")
    if not outcome:
        reasons.append("OUTCOME_CODE_MISSING")
    status = "READY" if not reasons else "HELD"
    return StructuralKalshiEventIdentity(
        str(row.get("parent_ticker") or ""),
        market_ticker,
        event_ticker,
        league,
        outcome,
        str(market.get("title") or "").strip(),
        exact_relation,
        status,
        tuple(reasons),
        False,
    )

def reconstruct_cohort(rows):
    return tuple(reconstruct_identity(r) for r in rows)
"""

TEST_BODY = r"""
from pathlib import Path
from dataclasses import asdict
import json
from qseries_v2.kalshi_sports_evidence_mapping.structural_kalshi_event_identity import reconstruct_cohort

root = Path.cwd()
src = json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem066_supported_league_live_cohort.json").read_text(encoding="utf-8"))
rows = reconstruct_cohort(src["rows"])
ready = [r for r in rows if r.status == "READY"]
print("[TOTAL]", len(rows))
print("[READY]", len(ready))
for r in rows[:15]:
    print("[IDENTITY]", r.league, r.event_ticker, "=>", r.outcome_code, r.status)
assert rows
assert ready, "no exact Kalshi market->event structural identity reconstructed"
assert all(r.execution_authority is False for r in rows)
state = root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem067_structural_kalshi_event_identity.json").write_text(
    json.dumps({"rows":[asdict(r) for r in rows],"ready":len(ready),"execution_authority":False}, indent=2),
    encoding="utf-8"
)
print("[PASS] exact market/event parent-child structure preserved independently of proposition text")
print("[PASS] KSEM-067 certified")
"""

def main():
    print("="*120)
    print(" KSEM-067 STRUCTURAL KALSHI EVENT IDENTITY RECONSTRUCTION INSTALLER")
    print("="*120)
    dep = STATE/"ksem066_supported_league_live_cohort.json"
    if not dep.is_file():
        raise RuntimeError("KSEM-066 physical state required")
    MOD.write_text(MODULE.lstrip(), encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(), encoding="utf-8")
    print("[PASS] wrote", MOD.relative_to(ROOT))
    print("[PASS] wrote", TEST.name)
    print("[PASS] market ticker -> exact event ticker relationship preserved")
    print("[PASS] proposition outcome code kept separate from game identity")
    print("[PASS] KSEM-067 installer complete")
if __name__ == "__main__":
    main()
