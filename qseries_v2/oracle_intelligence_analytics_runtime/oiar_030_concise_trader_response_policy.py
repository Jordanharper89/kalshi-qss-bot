
from __future__ import annotations
from .oiar_028_relative_strength_semantics import rank_relative,strongest_assessment
OIAR_030_BUILD_ID="OIAR-030"
OIAR_030_REVISION="OIAR_030_CONCISE_TRADER_RESPONSE_POLICY_V1"
EXECUTION_AUTHORITY=False
def _title(m):
    t=str(m.get("market_title") or "Identity unresolved")
    return t if len(t)<=150 else t[:147]+"..."
def render_concise(markets,intent,limit=2):
    ranked=rank_relative(markets)
    if intent.direction in ("bullish","bearish"):
        want="BULLISH" if intent.direction=="bullish" else "BEARISH"
        ranked=tuple(m for m in ranked if str(m.get("direction") or "").upper()==want)
    if intent.ranking=="strongest":
        a=strongest_assessment(ranked)
        if not a["market"]:return ("ORACLE READ: NOTHING TO RANK RIGHT NOW",)
        m=a["market"]
        return ("="*80,"ORACLE TRADER READ",a["message"],"-"*80,_title(m),f"Oracle read: {m.get('trader_takeaway')}",f"Direction: {m.get('direction')}",f"Why: {m.get('why')}",f"Trader take: {'Worth watching now.' if a['clears_edge'] else 'Watch it. Do not chase it yet.'}",f"Market ID: {m.get('market_id')}","="*80)
    edge=tuple(m for m in ranked if str(m.get("setup_status") or "")=="WORTH_WATCHING_NOW")
    forming=tuple(m for m in ranked if str(m.get("setup_status") or "")=="SETUP_FORMING")
    chosen=(edge or forming or ranked)[:max(1,min(int(limit),2))]
    lead=("ORACLE READ: PLAYS AVAILABLE" if edge else "ORACLE READ: SETUPS FORMING, NOTHING CONFIRMED" if forming else "ORACLE READ: NO EDGE RIGHT NOW")
    lines=["="*80,"ORACLE TRADER READ",lead,"-"*80]
    for i,m in enumerate(chosen,1):
        lines += [f"#{i} {_title(m)}",f"   Read: {m.get('trader_takeaway')} | Direction: {m.get('direction')}",f"   Why: {m.get('why')}",f"   Risk: {m.get('risk')}"]
    lines+=["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)
