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
