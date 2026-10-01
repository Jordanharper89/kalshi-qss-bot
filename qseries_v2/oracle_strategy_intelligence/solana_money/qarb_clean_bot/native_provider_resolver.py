
from __future__ import annotations
import ast,importlib.util,inspect
from dataclasses import dataclass
from pathlib import Path

BAD=("requests","urllib","http(","rpc(","urlopen","jupiter","subprocess","sleep(")
VENUE_HINTS={
 "RAYDIUM_CLMM":("raydium","clmm"),
 "ORCA_WHIRLPOOL":("orca","whirl"),
}
FN_HINTS=("quote","swap_quote","quote_exact_in","compute_swap","simulate_swap")

@dataclass(frozen=True)
class Candidate:
    venue:str
    module_path:str
    function:str
    score:int
    hot_io_free:bool

def scan(root,venue):
    root=Path(root);hints=VENUE_HINTS[venue];rows=[]
    q=root/"qseries_v2"
    if not q.exists(): return rows
    for p in q.rglob("*.py"):
        low=str(p).lower()
        if "qarb_clean_bot" in low:
            continue
        if not all(h in low for h in hints): continue
        try: src=p.read_text(encoding="utf-8");tree=ast.parse(src)
        except Exception: continue
        s=src.lower();iofree=not any(x in s for x in BAD)
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                name=n.name.lower()
                score=sum(4 for h in FN_HINTS if h in name)+sum(1 for h in hints if h in low)
                if score>=6:
                    rows.append(Candidate(venue,str(p.relative_to(root)),n.name,score,iofree))
    rows.sort(key=lambda x:(not x.hot_io_free,-x.score,x.module_path,x.function))
    return rows

def best(root,venue):
    rows=[x for x in scan(root,venue) if x.hot_io_free]
    return rows[0] if rows else None
