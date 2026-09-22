from pathlib import Path
ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "kalshi_sports_evidence_mapping"
STATE = PKG / "state"
MOD = PKG / "supported_league_live_cohort.py"
TEST = ROOT / "test_ksem_066_supported_league_live_cohort_selector.py"

MODULE = r"""
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
"""

TEST_BODY = r"""
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
"""

def main():
    print("="*120)
    print(" KSEM-066 SUPPORTED-LEAGUE LIVE COHORT SELECTOR INSTALLER")
    print("="*120)
    deps = [
        ROOT/"qseries_v2/oracle_adapters/independent/oad_069_current_open_kalshi_market_index.py",
        ROOT/"qseries_v2/kalshi_sports_evidence_mapping/exact_live_underlying_market_retrieval.py",
        ROOT/"qseries_v2/kalshi_sports_evidence_mapping/exact_live_sports_proposition_context.py",
    ]
    for dep in deps:
        if not dep.is_file():
            raise RuntimeError(f"missing dependency: {dep.relative_to(ROOT)}")
        print("[PASS] dependency verified:", dep.relative_to(ROOT))
    PKG.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE.lstrip(), encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(), encoding="utf-8")
    print("[PASS] wrote", MOD.relative_to(ROOT))
    print("[PASS] wrote", TEST.name)
    print("[PASS] supported-league selection occurs before exact Kalshi GET")
    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")
    print("[PASS] KSEM-066 installer complete")
if __name__ == "__main__":
    main()
