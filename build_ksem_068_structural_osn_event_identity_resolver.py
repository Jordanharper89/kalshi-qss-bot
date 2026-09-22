from pathlib import Path
ROOT = Path.cwd()
PKG = ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE = PKG/"state"
MOD = PKG/"structural_osn_event_identity_resolver.py"
TEST = ROOT/"test_ksem_068_structural_osn_event_identity_resolver.py"

MODULE = r"""
from dataclasses import dataclass
import re
from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False
ADMITTED = ("NFL","NCAAF","NBA","NHL","MLS","EPL")

@dataclass(frozen=True)
class StructuralOSNBinding:
    market_ticker: str
    event_ticker: str
    league: str
    status: str
    provider: str|None
    provider_event_id: str|None
    home_team: str|None
    away_team: str|None
    scheduled_start: str|None
    match_method: str|None
    candidate_count: int
    execution_authority: bool = False

def _norm(v):
    return re.sub(r"[^A-Z0-9]+", "", str(v or "").upper())

def _event_symbol(event_ticker):
    text = str(event_ticker or "").upper()
    if "-" not in text:
        return _norm(text)
    return _norm(text.rsplit("-", 1)[-1])

def _event_matches(symbol, event):
    home = _norm(getattr(event, "home_team", ""))
    away = _norm(getattr(event, "away_team", ""))
    if not home or not away:
        return False
    return symbol.endswith(away + home) or symbol.endswith(home + away)

def _single_team_overlap(symbol, event):
    home = _norm(getattr(event, "home_team", ""))
    away = _norm(getattr(event, "away_team", ""))
    return bool((home and home in symbol) or (away and away in symbol))

def resolve_one(identity, events):
    ticker = identity["market_ticker"]
    event_ticker = identity["event_ticker"]
    league = identity["league"]
    if identity.get("status") != "READY" or league not in ADMITTED:
        return StructuralOSNBinding(ticker,event_ticker,league,"UNSUPPORTED",None,None,None,None,None,None,0,False)
    symbol = _event_symbol(event_ticker)
    exact = [e for e in events if _event_matches(symbol, e)]
    if len(exact) == 1:
        e = exact[0]
        return StructuralOSNBinding(
            ticker,event_ticker,league,"EXACT_BOUND",
            str(getattr(e,"provider","") or ""),
            str(getattr(e,"provider_event_id","") or ""),
            str(getattr(e,"home_team","") or ""),
            str(getattr(e,"away_team","") or ""),
            str(getattr(e,"scheduled_start","") or ""),
            "STRUCTURAL_TEAM_PAIR_IN_EVENT_TICKER",1,False
        )
    if len(exact) > 1:
        return StructuralOSNBinding(ticker,event_ticker,league,"AMBIGUOUS",None,None,None,None,None,"MULTIPLE_STRUCTURAL_TEAM_PAIR_MATCHES",len(exact),False)
    partial = [e for e in events if _single_team_overlap(symbol, e)]
    if partial:
        return StructuralOSNBinding(ticker,event_ticker,league,"PARTIAL",None,None,None,None,None,"ONE_TEAM_STRUCTURAL_OVERLAP",len(partial),False)
    return StructuralOSNBinding(ticker,event_ticker,league,"SOURCE_GAP",None,None,None,None,None,"NO_STRUCTURAL_OSN_EVENT_MATCH",0,False)

def resolve_cohort(identity_rows, root=None, timeout_seconds=15):
    leagues = sorted({r.get("league") for r in identity_rows if r.get("league") in ADMITTED})
    events_by_league = {}
    for league in leagues:
        result = acquire_canonical_events(league, timeout=timeout_seconds, root=root)
        events_by_league[league] = tuple(result.events)
    bindings = tuple(resolve_one(r, events_by_league.get(r.get("league"), ())) for r in identity_rows)
    return bindings, events_by_league
"""

TEST_BODY = r"""
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
"""

def main():
    print("="*120)
    print(" KSEM-068 STRUCTURAL OSN EVENT IDENTITY RESOLVER INSTALLER")
    print("="*120)
    dep = STATE/"ksem067_structural_kalshi_event_identity.json"
    if not dep.is_file():
        raise RuntimeError("KSEM-067 physical state required")
    provider = ROOT/"qseries_v2/oracle_source_network/providers/uniform_sports_provider.py"
    if not provider.is_file():
        raise RuntimeError("uniform sports provider missing")
    print("[PASS] dependency verified:", provider.relative_to(ROOT))
    MOD.write_text(MODULE.lstrip(), encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(), encoding="utf-8")
    print("[PASS] wrote", MOD.relative_to(ROOT))
    print("[PASS] wrote", TEST.name)
    print("[PASS] exact structural team-pair match required for EXACT_BOUND")
    print("[PASS] no broad alias table introduced")
    print("[PASS] KSEM-068 installer complete")
if __name__ == "__main__":
    main()
