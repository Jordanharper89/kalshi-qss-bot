from __future__ import annotations
from dataclasses import dataclass
import re
from qseries_v2.oracle_adapters.independent.oad_096_atomic_sports_admission_boundary import atomic_sports_admission

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class CrossCategoryLeg:
    parent_ticker:str
    leg_index:int
    polarity:str
    text:str
    domain:str
    sport:str
    league:str
    state:str

def _title(market):
    return str(market.get("title","") or "").strip()

def split_cross_category_legs(market):
    ticker=str(market.get("ticker",""))
    title=_title(market)
    if not title:
        return ()
    pieces=[x.strip() for x in re.split(r",(?=\s*(?:yes|no)\b)", title, flags=re.I) if x.strip()]
    if len(pieces)==1 and not re.match(r"^(yes|no)\b", pieces[0], re.I):
        pieces=[pieces[0]]
    out=[]
    for i,piece in enumerate(pieces,1):
        m=re.match(r"^(yes|no)\s+(.*)$",piece,re.I)
        polarity=m.group(1).lower() if m else "unspecified"
        text=m.group(2).strip() if m else piece
        synthetic=dict(market)
        synthetic["title"]=text
        synthetic["yes_sub_title"]=""
        synthetic["no_sub_title"]=""
        admission=atomic_sports_admission(synthetic)
        out.append(CrossCategoryLeg(ticker,i,polarity,text,admission.admitted_domain,admission.sport,admission.league,admission.state))
    return tuple(out)
