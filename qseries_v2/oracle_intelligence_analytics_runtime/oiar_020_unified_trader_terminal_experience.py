from __future__ import annotations
from pathlib import Path

from .oiar_009_fast_terminal_read_adapter import read_fast_trader_intelligence
from .oiar_018_trader_opportunity_explanation import explain_trader_opportunity
from .oiar_019_trader_followup_intelligence import answer_followup

OIAR_020_BUILD_ID="OIAR-020"
OIAR_020_REVISION="OIAR_020_UNIFIED_TRADER_TERMINAL_EXPERIENCE_V1"

QUERY_TOKENS=("what do you like","best markets","anything worth","what should i watch","edge right now","historically proven","live opportunities","rank trader intelligence")

def is_unified_trader_query(q):
    n=" ".join(str(q or "").lower().split())
    return any(t in n for t in QUERY_TOKENS)

def render_unified_trader_answer(root,query,limit=5):
    snap=read_fast_trader_intelligence(Path(root).resolve(),20)
    rows=snap.rows[:max(1,min(int(limit),10))]
    lines=["="*80,"ORACLE TRADER BRIEF","-"*80]
    if snap.freshness_status!="FRESH":
        lines.append(f"Data warning: {snap.freshness_status} snapshot, age {snap.age_seconds:.0f}s.")
        lines.append("Do not treat this as a live trading signal.")
        lines.append("-"*80)

    if not rows:
        lines.append("Oracle has no ranked markets in the current persisted snapshot.")
    else:
        strong=[r for r in rows if str(r.admission_status).lower()=="admitted"]
        if not strong:
            lines.append("Nothing in this snapshot clears Oracle's current edge threshold.")
            lines.append("")
        for i,row in enumerate(rows,1):
            e=explain_trader_opportunity(root,row)
            lines += [
                f"#{i} {e.headline}",
                f"   Why: {e.why}",
                f"   What would improve it: {e.what_would_improve_it}",
                f"   Main risk: {e.main_risk}",
                f"   Trader takeaway: {e.takeaway}",
                f"   Market ID: {row.market_id}",
                ""
            ]
    lines += ["No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)

def bind_unified_trader_experience(base_module,root=None):
    if getattr(base_module,"_oiar020_bound",False):return base_module
    original=base_module.display_query
    active=Path(root or base_module.repository_root()).resolve()

    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query)
        use=Path(root or active).resolve()
        if is_unified_trader_query(canonical):
            for line in render_unified_trader_answer(use,canonical,5):
                write(line)
            return None
        kwargs={"session":session,"root":use,"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)

    base_module.display_query=display_query
    base_module._oiar020_bound=True
    return base_module
