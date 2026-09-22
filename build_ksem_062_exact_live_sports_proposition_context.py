from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state"
MOD=PKG/"exact_live_sports_proposition_context.py"
TEST=ROOT/"test_ksem_062_exact_live_sports_proposition_context.py"

MODULE=r"""
import re
from dataclasses import dataclass,asdict
from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SUPPORTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")

@dataclass(frozen=True)
class ExactSportsPropositionContext:
    parent_ticker:str
    market_ticker:str
    event_ticker:str
    side:str
    league:str|None
    proposition_type:str
    title:str
    subtitle:str
    yes_sub_title:str
    no_sub_title:str
    status:str
    reasons:tuple
    execution_authority:bool=False

def infer_league(ticker,event_ticker,title=""):
    text=" ".join((str(ticker),str(event_ticker),str(title))).upper()
    rules=(
        ("NCAAF",("KXNCAAF","NCAAF")),
        ("NFL",("KXNFL"," NFL ")),
        ("NBA",("KXNBA"," NBA ")),
        ("NHL",("KXNHL"," NHL ")),
        ("EPL",("KXEPL","PREMIER LEAGUE")),
        ("MLS",("KXMLS"," MLS ")),
    )
    hits=[league for league,terms in rules if any(term in f" {text} " for term in terms)]
    return hits[0] if len(set(hits))==1 else None

def reconstruct(row):
    market=dict(row.get("market") or {})
    ticker=str(row.get("market_ticker") or market.get("ticker") or "").strip().upper()
    event=str(row.get("event_ticker") or market.get("event_ticker") or "").strip().upper()
    title=str(market.get("title") or market.get("market_title") or "").strip()
    subtitle=str(market.get("subtitle") or "").strip()
    yes=str(market.get("yes_sub_title") or "").strip()
    no=str(market.get("no_sub_title") or "").strip()
    league=infer_league(ticker,event,title)
    mt=resolve_sports_market_type(market)
    ptype=str(getattr(mt,"market_type","sports_other"))
    reasons=[]
    if row.get("status")!="RESOLVED": reasons.append("EXACT_MARKET_NOT_RESOLVED")
    if not league: reasons.append("SUPPORTED_LEAGUE_NOT_RESOLVED")
    if ptype in ("non_sports","sports_other"): reasons.append("PROPOSITION_TYPE_NOT_EXACT")
    status="READY" if not reasons else "HELD"
    return ExactSportsPropositionContext(
        str(row.get("parent_ticker") or ""),ticker,event,str(row.get("side") or ""),
        league,ptype,title,subtitle,yes,no,status,tuple(reasons),False)

def reconstruct_rows(rows):
    return tuple(reconstruct(r) for r in rows)
"""

TEST_BODY=r"""
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
"""

def main():
    print("="*120); print(" KSEM-062 EXACT LIVE SPORTS PROPOSITION CONTEXT INSTALLER"); print("="*120)
    if not (STATE/"ksem061_exact_live_underlying_market_retrieval.json").exists():
        raise RuntimeError("KSEM-061 physical state required")
    MOD.write_text(MODULE.lstrip(),encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",TEST.name)
    print("[PASS] exact market payload -> league/proposition context boundary installed")
    print("[PASS] KSEM-062 installer complete")
if __name__=="__main__": main()
