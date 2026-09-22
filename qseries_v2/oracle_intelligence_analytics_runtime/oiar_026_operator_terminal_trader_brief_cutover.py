
from __future__ import annotations
from pathlib import Path
from .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief

OIAR_026_BUILD_ID="OIAR-026"
OIAR_026_REVISION="OIAR_026_OPERATOR_TERMINAL_TRADER_BRIEF_CUTOVER_V1"
TOKENS=("what do you like","best markets","anything worth","what should i watch","edge right now","historically proven","live opportunities","rank trader intelligence")

def is_trader_brief_query(q):
    n=" ".join(str(q or "").lower().split())
    return any(t in n for t in TOKENS)

def render_trader_brief(root,limit=5):
    x=read_fast_trader_brief(root,limit)
    lines=["="*80,"ORACLE TRADER BRIEF","SNAPSHOT-ONLY | PRECOMPUTED INTELLIGENCE","-"*80]
    markets=x.markets[:limit]
    if not any(str(m.get("trader_takeaway") or "")=="WORTH WATCHING NOW" for m in markets):
        lines+=["Nothing in this snapshot clears Oracle's current edge threshold.",""]
    for i,m in enumerate(markets,1):
        lines += [
            f"#{i} {m.get('market_title') or 'Identity unresolved'}",
            f"   Oracle read: {m.get('trader_takeaway')}",
            f"   Direction: {m.get('direction')}",
            f"   Historical knowledge: {m.get('historical_strength')} | Live evidence: {m.get('live_evidence')}",
            f"   Why: {m.get('why')}",
            f"   What would improve it: {m.get('what_would_improve_it')}",
            f"   Risk: {m.get('risk')}",
            f"   Market ID: {m.get('market_id')}",
            ""
        ]
    lines+=["No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)

def bind_trader_brief_terminal(base_module,root=None):
    if getattr(base_module,"_oiar026_bound",False):return base_module
    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query);use=Path(root or active).resolve()
        if is_trader_brief_query(canonical):
            for line in render_trader_brief(use,5):write(line)
            return None
        kwargs={"session":session,"root":use,"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)
    base_module.display_query=display_query;base_module._oiar026_bound=True
    return base_module
