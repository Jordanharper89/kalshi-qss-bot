from __future__ import annotations
from pathlib import Path
from .oiar_059_thesis_calibration_readiness import read_latest_thesis_calibration_readiness

OIAR_060_BUILD_ID="OIAR-060"
TOKENS=("why do you like","build a thesis","what is the thesis","thesis for","why is this strong","evidence for")

def is_thesis_query(q):
    n=" ".join(str(q or "").lower().split())
    return any(t in n for t in TOKENS)

def render_thesis_surface(root=None,limit=5):
    x=read_latest_thesis_calibration_readiness(root)
    if not x:raise RuntimeError("OIAR-060 requires OIAR-059 snapshot")
    rows=x.get("markets",[])[:max(1,min(int(limit),10))]
    lines=["="*80,"ORACLE THESIS RESEARCH","EVIDENCE COMBINATION | CALIBRATION-GATED | READ ONLY","-"*80]
    for i,r in enumerate(rows,1):
        lines += [
            f"#{i} {r.get('title') or r.get('market_id')}",
            f"   Market: {r.get('market_id')}",
            f"   Direction: {str(r.get('direction','neutral')).upper()}",
            f"   Thesis: {r.get('thesis_statement')}",
            f"   Calibration: {r.get('calibration_status')} ({r.get('settled_outcomes',0)}/{r.get('minimum_outcomes_required',30)} settled outcomes)",
            "   Probability: UNAVAILABLE" if r.get("empirical_rate") is None else f"   Historical rate: {r['empirical_rate']}",
            "   Trader take: Research only; no execution authority.",
            ""
        ]
    lines += ["Oracle will not invent a probability until settled-outcome calibration exists.",
              "No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)

def physical_probe(root=None):
    lines=render_thesis_surface(root,5)
    return {"lines":len(lines),"header":lines[1],"execution_authority":False}
