from __future__ import annotations
from dataclasses import dataclass
from .oiar_018_trader_opportunity_explanation import explain_trader_opportunity

OIAR_019_BUILD_ID="OIAR-019"
OIAR_019_REVISION="OIAR_019_TRADER_FOLLOWUP_INTELLIGENCE_V1"

@dataclass(frozen=True)
class TraderFollowupAnswer:
    question_type:str
    lines:tuple
    read_only:bool=True
    execution_authority:bool=False

def classify_followup(query):
    q=" ".join(str(query or "").lower().split())
    if "why" in q:return "WHY"
    if "change your mind" in q or "what would improve" in q:return "IMPROVE"
    if "risk" in q or "fail" in q:return "RISK"
    if "learned" in q:return "LEARNED"
    return "SUMMARY"

def answer_followup(root,row,query):
    e=explain_trader_opportunity(root,row)
    kind=classify_followup(query)
    if kind=="WHY": lines=(e.headline,e.why)
    elif kind=="IMPROVE": lines=(e.headline,e.what_would_improve_it)
    elif kind=="RISK": lines=(e.headline,e.main_risk)
    elif kind=="LEARNED":
        lines=(e.headline,f"Historical maturity={row.maturity}; reliability={float(row.reliability or 0):.3f}; learned family records={int(row.learned_family_records or 0)}.")
    else: lines=(e.headline,e.why,e.main_risk,e.takeaway)
    return TraderFollowupAnswer(kind,lines,True,False)
