from dataclasses import dataclass
from datetime import datetime, timezone
import re
from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False
ADMITTED = ("NFL","NCAAF","NBA","NHL","MLS","EPL")
MONTHS = {
    "JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
    "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12,
}

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

def _words(v):
    return tuple(x for x in re.findall(r"[A-Z0-9]+", str(v or "").upper()) if x)

def _event_symbol(event_ticker):
    text = str(event_ticker or "").upper()
    return _norm(text.rsplit("-",1)[-1] if "-" in text else text)

def _event_date(event_ticker):
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})", str(event_ticker or "").upper())
    if not m or m.group(2) not in MONTHS:
        return None
    return f"20{m.group(1)}-{MONTHS[m.group(2)]:02d}-{int(m.group(3)):02d}"

def _scheduled_date(event):
    raw = str(getattr(event,"scheduled_start","") or "")
    if len(raw) >= 10:
        return raw[:10]
    return None

def _team_tokens(team):
    words = _words(team)
    compact = _norm(team)
    out = set(words)
    if compact:
        out.add(compact)
    return out

def _title_team_hit(title, event):
    title_words = set(_words(title))
    title_compact = _norm(title)
    hits = []
    for side, team in (("HOME",getattr(event,"home_team","")),("AWAY",getattr(event,"away_team",""))):
        tokens = _team_tokens(team)
        strong = any(len(t) >= 3 and (t in title_words or t in title_compact) for t in tokens)
        if strong:
            hits.append(side)
    return tuple(hits)

def _structural_pair_hit(symbol, event):
    home = _norm(getattr(event,"home_team",""))
    away = _norm(getattr(event,"away_team",""))
    if not home or not away:
        return False
    return symbol.endswith(away+home) or symbol.endswith(home+away)

def resolve_one(identity, events):
    ticker = str(identity.get("market_ticker") or "")
    event_ticker = str(identity.get("event_ticker") or "")
    league = str(identity.get("league") or "")
    title = str(identity.get("title") or "")
    if identity.get("status") != "READY" or league not in ADMITTED:
        return StructuralOSNBinding(ticker,event_ticker,league,"UNSUPPORTED",None,None,None,None,None,None,0,False)

    symbol = _event_symbol(event_ticker)
    kalshi_date = _event_date(event_ticker)
    same_date = [e for e in events if kalshi_date and _scheduled_date(e) == kalshi_date]

    structural = [e for e in same_date if _structural_pair_hit(symbol,e)]
    if len(structural) == 1:
        e = structural[0]
        return StructuralOSNBinding(
            ticker,event_ticker,league,"EXACT_BOUND",
            str(getattr(e,"provider","") or ""),
            str(getattr(e,"provider_event_id","") or ""),
            str(getattr(e,"home_team","") or ""),
            str(getattr(e,"away_team","") or ""),
            str(getattr(e,"scheduled_start","") or ""),
            "LEAGUE_DATE_STRUCTURAL_TEAM_PAIR",1,False
        )
    if len(structural) > 1:
        return StructuralOSNBinding(ticker,event_ticker,league,"AMBIGUOUS",None,None,None,None,None,"MULTIPLE_DATE_STRUCTURAL_MATCHES",len(structural),False)

    titled = [e for e in same_date if _title_team_hit(title,e)]
    if len(titled) == 1:
        e = titled[0]
        return StructuralOSNBinding(
            ticker,event_ticker,league,"EXACT_BOUND",
            str(getattr(e,"provider","") or ""),
            str(getattr(e,"provider_event_id","") or ""),
            str(getattr(e,"home_team","") or ""),
            str(getattr(e,"away_team","") or ""),
            str(getattr(e,"scheduled_start","") or ""),
            "LEAGUE_DATE_UNIQUE_PROPOSITION_TEAM",1,False
        )
    if len(titled) > 1:
        return StructuralOSNBinding(ticker,event_ticker,league,"AMBIGUOUS",None,None,None,None,None,"MULTIPLE_DATE_TITLE_TEAM_MATCHES",len(titled),False)

    any_date = len(same_date)
    any_team = sum(bool(_title_team_hit(title,e)) for e in events)
    if any_date and any_team:
        return StructuralOSNBinding(ticker,event_ticker,league,"PARTIAL",None,None,None,None,None,"DATE_AND_TEAM_EVIDENCE_DO_NOT_UNIQUELY_INTERSECT",max(any_date,any_team),False)
    if any_date:
        return StructuralOSNBinding(ticker,event_ticker,league,"PARTIAL",None,None,None,None,None,"EXACT_DATE_ONLY",any_date,False)
    if any_team:
        return StructuralOSNBinding(ticker,event_ticker,league,"PARTIAL",None,None,None,None,None,"PROPOSITION_TEAM_ONLY",any_team,False)
    return StructuralOSNBinding(ticker,event_ticker,league,"SOURCE_GAP",None,None,None,None,None,"NO_OSN_IDENTITY_EVIDENCE",0,False)

def resolve_cohort(identity_rows, root=None, timeout_seconds=15):
    leagues = sorted({r.get("league") for r in identity_rows if r.get("league") in ADMITTED})
    events_by_league = {}
    for league in leagues:
        result = acquire_canonical_events(league, timeout=timeout_seconds, root=root)
        events_by_league[league] = tuple(result.events)
    bindings = tuple(resolve_one(r,events_by_league.get(r.get("league"),())) for r in identity_rows)
    return bindings, events_by_league
