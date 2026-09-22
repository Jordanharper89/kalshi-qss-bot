from __future__ import annotations
from pathlib import Path
from .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief
from .oiar_027_trader_intent_classifier import classify_trader_intent
from .oiar_028_relative_strength_semantics import rank_relative
from .oiar_032_market_name_compression import compress_market_name
from .oiar_033_event_sport_context import classify_event_context
from .oiar_034_temporal_relevance import temporal_relevance
from .oiar_035_conversational_followup_resolution import classify_followup,followup_kind,ordinal_index
OIAR_036_BUILD_ID="OIAR-036"
OIAR_036_REVISION="OIAR_036_TRADER_CARD_PRESENTATION_CUTOVER_V1"
EXECUTION_AUTHORITY=False
_STATE={"markets":(),"selected":0}

def _card(m,rank=1):
    ctx=classify_event_context(m);tm=temporal_relevance(m)
    return (
      f"#{rank} {compress_market_name(m)}",
      f"   Market: {ctx['sport']} | Time: {tm['label']}",
      f"   Read: {m.get('trader_takeaway') or 'NO EDGE RIGHT NOW'} | Direction: {m.get('direction') or 'NEUTRAL'}",
      f"   Why: {m.get('why') or 'Live evidence has not confirmed an edge.'}",
      f"   Risk: {m.get('risk') or 'UNKNOWN'}",
      f"   Trader take: {'Worth watching.' if str(m.get('setup_status')) in ('WORTH_WATCHING_NOW','SETUP_FORMING') else 'Watch only. Do not chase it.'}",
    )

def render_trader_cards(markets,limit=2):
    ranked=rank_relative(markets);chosen=ranked[:max(1,min(int(limit),2))]
    _STATE["markets"]=tuple(chosen);_STATE["selected"]=0
    edge=any(str(x.get("setup_status") or "")=="WORTH_WATCHING_NOW" for x in chosen)
    lead="Oracle has something worth watching." if edge else "Nothing clears Oracle's edge threshold right now."
    lines=["="*80,"ORACLE TRADER READ",lead,"-"*80]
    for i,m in enumerate(chosen,1):lines.extend(_card(m,i))
    lines+=["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)

def render_followup(query):
    markets=_STATE.get("markets") or ()
    if not markets:return ("I do not have an active trader read to follow up on yet.",)
    idx=ordinal_index(query)
    if idx is not None and idx<len(markets):_STATE["selected"]=idx
    m=markets[min(_STATE.get("selected",0),len(markets)-1)]
    kind=followup_kind(query)
    if kind=="time":
        t=temporal_relevance(m)
        if not t["proven"]:return ("Oracle cannot prove from this snapshot that this market is for today.","Time relevance: UNKNOWN")
        return (f"Time relevance: {t['label']}",f"Snapshot event time: {t['event_time']}")
    if kind=="why":return (f"Why: {m.get('why') or 'Live evidence has not confirmed an edge.'}",)
    if kind=="risk":return (f"Risk: {m.get('risk') or 'UNKNOWN'}",)
    return _card(m,_STATE.get("selected",0)+1)

def bind_trader_card_terminal(base_module,root=None):
    if getattr(base_module,"_oiar036_bound",False):return base_module
    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query)
        if classify_followup(canonical):
            for line in render_followup(canonical):write(line)
            return None
        intent=classify_trader_intent(canonical)
        if intent.route=="trader_brief":
            x=read_fast_trader_brief(Path(root or active).resolve(),50)
            for line in render_trader_cards(x.markets,2):write(line)
            return None
        kwargs={"session":session,"root":Path(root or active).resolve(),"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)
    base_module.display_query=display_query;base_module._oiar036_bound=True
    return base_module
