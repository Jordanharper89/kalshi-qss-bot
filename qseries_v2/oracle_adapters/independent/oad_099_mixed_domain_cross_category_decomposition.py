from __future__ import annotations
from dataclasses import dataclass
import re
from qseries_v2.oracle_adapters.independent.oad_097_cross_category_leg_parser import split_cross_category_legs
from qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition import recognize_sports_entity_type
from qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class DecomposedLeg:
    parent_ticker:str
    leg_index:int
    polarity:str
    text:str
    domain:str
    subdomain:str
    state:str

def _non_sports_override(text):
    low=text.lower()
    if "target price:" in low or re.search(r"\$\s*\d",text):
        return "financial_price"
    return ""

def decompose_mixed_market(market):
    rows=split_cross_category_legs(market)
    out=[]
    for leg in rows:
        override=_non_sports_override(leg.text)
        if override:
            out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,"financial_markets",override,"RESOLVED"))
            continue
        entity=recognize_sports_entity_type(leg.text)
        if leg.domain=="sports" or entity.entity_type!="UNRESOLVED":
            sub=leg.league if leg.league not in ("NONE","") else "UNKNOWN"
            out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,"sports",sub,"RESOLVED" if sub!="UNKNOWN" else "UNRESOLVED"))
            continue
        synthetic=dict(market);synthetic["title"]=leg.text;synthetic["yes_sub_title"]="";synthetic["no_sub_title"]=""
        d=expanded_domain_classify(synthetic)
        out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,d.domain,"", "RESOLVED" if d.domain!="other" else "UNRESOLVED"))
    return tuple(out)
