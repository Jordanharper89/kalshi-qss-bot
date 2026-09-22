from __future__ import annotations
from dataclasses import dataclass
from .oiar_017_trader_market_context_model import build_trader_market_context

OIAR_018_BUILD_ID="OIAR-018"
OIAR_018_REVISION="OIAR_018_TRADER_OPPORTUNITY_EXPLANATION_V1"

@dataclass(frozen=True)
class TraderOpportunityExplanation:
    market_id:str
    headline:str
    why:str
    what_would_improve_it:str
    main_risk:str
    takeaway:str
    read_only:bool=True
    execution_authority:bool=False

def explain_trader_opportunity(root,row):
    c=build_trader_market_context(root,row)
    if c.identity_status!="RESOLVED":
        headline="Oracle cannot verify the exact market identity yet."
    elif c.setup_quality=="ACTIONABLE_RESEARCH":
        headline=f"{c.display_name}: worth watching now."
    elif c.setup_quality=="FORMING":
        headline=f"{c.display_name}: setup is forming."
    else:
        headline=f"{c.display_name}: no confirmed edge right now."

    if c.historical_strength=="STRONG" and c.live_evidence in ("WEAK","DEVELOPING"):
        why="Oracle knows this market family well, but current live evidence is not strong enough to confirm a setup."
    elif c.live_evidence=="STRONG":
        why="Current live evidence is substantial enough for Oracle to evaluate the setup with more confidence."
    else:
        why="Oracle has limited support from both historical and live evidence."

    improve="More live history and a directional setup that clears Oracle's usefulness/candidate thresholds."
    risk="The current evidence may be too thin or unstable to support a reliable directional call."
    takeaway="WORTH WATCHING NOW" if c.setup_quality=="ACTIONABLE_RESEARCH" else "WATCH - SETUP FORMING" if c.setup_quality=="FORMING" else "NO EDGE RIGHT NOW"

    return TraderOpportunityExplanation(row.market_id,headline,why,improve,risk,takeaway,True,False)
