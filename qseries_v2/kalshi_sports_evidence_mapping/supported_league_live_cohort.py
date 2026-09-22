from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_underlying_market_retrieval import retrieve_exact_market
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_sports_proposition_context import infer_league

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False
ADMITTED = ("NFL","NCAAF","NBA","NHL","MLS","EPL")

def _legs(parent):
    rows = parent.get("mve_selected_legs") or ()
    return tuple(x for x in rows if isinstance(x, dict))

def _leg_ticker(leg):
    return str(leg.get("market_ticker") or "").strip().upper()

def select_supported_live_cohort(root=None, universe_limit=1000, max_supported=40, timeout_seconds=15):
    root = Path(root or Path.cwd()).resolve()
    markets, _ = fetch_current_open_kalshi_market_index(
        root=root, limit=universe_limit, timeout_seconds=timeout_seconds
    )
    candidates = []
    seen = set()
    for parent in markets:
        for leg in _legs(parent):
            ticker = _leg_ticker(leg)
            if not ticker or ticker in seen:
                continue
            league = infer_league(ticker, str(leg.get("event_ticker") or ""), "")
            if league not in ADMITTED:
                continue
            seen.add(ticker)
            candidates.append({
                "parent_ticker": str(parent.get("ticker") or ""),
                "leg_index": leg.get("leg_index"),
                "market_ticker": ticker,
                "leg_event_ticker": str(leg.get("event_ticker") or "").strip().upper(),
                "side": str(leg.get("side") or "").strip().lower(),
                "league_hint": league,
            })
            if len(candidates) >= int(max_supported):
                break
        if len(candidates) >= int(max_supported):
            break
    if not candidates:
        return ()
    credentials = load_kalshi_credentials(root=root)
    rows = []
    for item in candidates:
        try:
            market = retrieve_exact_market(credentials, item["market_ticker"], timeout_seconds)
            status = "RESOLVED" if market else "NOT_FOUND"
            error = ""
        except Exception as exc:
            market = None
            status = "ERROR"
            error = f"{type(exc).__name__}: {exc}"
        rows.append({**item, "status": status, "market": market, "error": error})
    return tuple(rows)
